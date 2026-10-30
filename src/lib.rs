//! Python adapter for the owned portable TextForge API.
//!
//! ```
//! use textforge::api::portable::{Argument, InstructionSpec, PipelinePlan};
//! let mut plan = PipelinePlan::new();
//! plan.add(InstructionSpec::new("ate".into(), vec![Argument::Text("!".into())]))?;
//! assert_eq!(plan.compile()?.process("é")?, "é!");
//! # Ok::<(), textforge::api::portable::BindingError>(())
//! ```
mod buffers;
mod observers;
mod paths;
mod processor;

use pyo3::IntoPyObjectExt;
use pyo3::{
    exceptions::PyTypeError,
    prelude::*,
    types::{PyBool, PyInt, PyString, PyTuple},
};
use textforge::api::portable::{self, Argument, BindingError, InstructionSpec, PipelinePlan};

pyo3::create_exception!(_native, TextForgeError, pyo3::exceptions::PyException);

fn error(py: Python<'_>, error: BindingError) -> PyErr {
    let exception = TextForgeError::new_err(error.to_string());
    let value = exception.value(py);
    let attributes = (|| -> PyResult<()> {
        value.setattr("stage", format!("{:?}", error.stage).to_lowercase())?;
        value.setattr("code", error.code)?;
        value.setattr("message", error.message)?;
        value.setattr("instruction", error.instruction)?;
        value.setattr("input", error.input)?;
        Ok(())
    })();
    match attributes {
        Ok(()) => exception,
        Err(error) => error,
    }
}

/// Explicit execution-context reference; Python example: `Variable("name")`.
#[pyclass(name = "Variable", module = "textforge", frozen, get_all)]
#[derive(Clone)]
struct Variable {
    name: String,
}
#[pymethods]
impl Variable {
    #[new]
    fn new(name: String) -> Self {
        Self { name }
    }
    fn __repr__(&self) -> String {
        format!("Variable({:?})", self.name)
    }
}

fn argument(value: &Bound<'_, PyAny>) -> PyResult<Argument> {
    if value.is_instance_of::<PyBool>() {
        return Err(PyTypeError::new_err(
            "bool is not a TextForge numeric argument",
        ));
    }
    if value.is_instance_of::<PyString>() {
        return Ok(Argument::Text(value.extract()?));
    }
    if value.is_instance_of::<PyInt>() {
        return Ok(Argument::Number(value.extract()?));
    }
    if let Ok(reference) = value.extract::<PyRef<'_, Variable>>() {
        return Ok(Argument::Variable(reference.name.clone()));
    }
    if let Ok(instruction) = value.extract::<PyRef<'_, Instruction>>() {
        return Ok(Argument::Instruction(Box::new(instruction.spec.clone())));
    }
    Err(PyTypeError::new_err(
        "expected str, nonnegative int, Variable, or Instruction",
    ))
}

/// Owned instruction description; Python example: `Instruction("atb", "🍌")`.
#[pyclass(name = "Instruction", module = "textforge", frozen)]
struct Instruction {
    spec: InstructionSpec,
    depth: usize,
}

impl Instruction {
    fn from_spec(spec: InstructionSpec) -> Self {
        let mut pending = vec![(&spec, 0)];
        let mut depth = 0;
        while let Some((instruction, current)) = pending.pop() {
            depth = depth.max(current);
            for argument in &instruction.arguments {
                if let Argument::Instruction(child) = argument {
                    pending.push((child, current + 1));
                }
            }
        }
        Self { spec, depth }
    }
}
#[pymethods]
impl Instruction {
    #[new]
    #[pyo3(signature = (name, *arguments))]
    fn new(name: String, arguments: &Bound<'_, PyTuple>) -> PyResult<Self> {
        let mut values = Vec::with_capacity(arguments.len());
        let mut depth = 0;
        for item in arguments.iter() {
            if let Ok(child) = item.extract::<PyRef<'_, Instruction>>() {
                depth = depth.max(child.depth + 1);
                if depth > 32 {
                    return Err(PyTypeError::new_err("instruction nesting exceeds 32"));
                }
            }
            values.push(argument(&item)?);
        }
        Ok(Self {
            spec: InstructionSpec::new(name, values),
            depth,
        })
    }
    #[getter]
    fn name(&self) -> &str {
        &self.spec.name
    }
    #[getter]
    fn arguments<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        let values: PyResult<Vec<Py<PyAny>>> = self
            .spec
            .arguments
            .iter()
            .map(|argument| match argument {
                Argument::Text(value) => value.into_py_any(py),
                Argument::Number(value) => value.into_py_any(py),
                Argument::Variable(name) => {
                    Py::new(py, Variable { name: name.clone() }).map(Py::into_any)
                }
                Argument::Instruction(spec) => {
                    Py::new(py, Instruction::from_spec((**spec).clone())).map(Py::into_any)
                }
                _ => Err(PyTypeError::new_err(
                    "unsupported portable argument variant",
                )),
            })
            .collect();
        PyTuple::new(py, values?)
    }
    fn __repr__(&self) -> String {
        format!("Instruction({:?}, ...)", self.spec.name)
    }
}

/// Temporary owned lowering plan, built by the Python facade.
/// See `textforge.Pipeline` for examples.
#[pyclass(module = "textforge._native")]
#[derive(Default)]
struct Plan {
    inner: PipelinePlan,
}
#[pymethods]
impl Plan {
    #[new]
    fn new() -> Self {
        Self::default()
    }
    fn add(&mut self, py: Python<'_>, instruction: &Instruction) -> PyResult<()> {
        self.inner
            .add(instruction.spec.clone())
            .map_err(|e| error(py, e))
    }
    fn block(&mut self, name: String, body: &mut Self) {
        self.inner.block(name, std::mem::take(&mut body.inner));
    }
    fn contains_each(&mut self, pattern: String, body: &mut Self) {
        self.inner
            .contains_each(pattern, std::mem::take(&mut body.inner));
    }
    fn compile(&self, py: Python<'_>) -> PyResult<CompiledPipeline> {
        self.inner
            .compile()
            .map(|inner| CompiledPipeline { inner })
            .map_err(|e| error(py, e))
    }
}

/// Independent reusable executable; Python: `Pipeline(...).compile().process("x")`.
#[pyclass(module = "textforge", frozen)]
struct CompiledPipeline {
    inner: portable::CompiledPipeline,
}
#[pymethods]
impl CompiledPipeline {
    fn process(&self, py: Python<'_>, input: &str) -> PyResult<String> {
        py.detach(|| self.inner.process(input))
            .map_err(|e| error(py, e))
    }
    fn __call__(&self, py: Python<'_>, input: &str) -> PyResult<String> {
        self.process(py, input)
    }
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<Variable>()?;
    module.add_class::<Instruction>()?;
    module.add_class::<Plan>()?;
    module.add_class::<CompiledPipeline>()?;
    module.add_class::<processor::Processor>()?;
    module.add_class::<paths::FilePath>()?;
    module.add_class::<paths::Features>()?;
    module.add_class::<paths::BatchPool>()?;
    module.add_class::<buffers::BufferOptions>()?;
    module.add_class::<buffers::PortableBuffer>()?;
    module.add_class::<observers::Observation>()?;
    module.add_class::<observers::Observers>()?;
    module.add_function(wrap_pyfunction!(paths::features, module)?)?;
    let exception_type = module.py().get_type::<TextForgeError>();
    exception_type.setattr("__module__", "textforge")?;
    module.add("TextForgeError", exception_type)?;
    module.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
