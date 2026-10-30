use super::*;
use crate::{
    buffers::{BufferOptions, PortableBuffer},
    observers::Observers,
    paths::{BatchPool, FilePath},
};
use textforge::api::portable::PortableProcessor;

/// Registry and file processor; Python: `processor = Processor()`.
#[pyclass(module = "textforge")]
#[derive(Default)]
pub(super) struct Processor {
    inner: PortableProcessor,
}
#[pymethods]
impl Processor {
    #[new]
    fn new() -> Self {
        Self::default()
    }
    fn register(&mut self, py: Python<'_>, plan: &Plan) -> PyResult<String> {
        self.inner.register(&plan.inner).map_err(|e| error(py, e))
    }
    fn remove_transform(&mut self, py: Python<'_>, id: &str) -> PyResult<()> {
        self.inner.remove_transform(id).map_err(|e| error(py, e))
    }
    fn transform_exists(&self, id: &str) -> bool {
        self.inner.transform_exists(id)
    }
    fn list_transforms(&self) -> Vec<String> {
        self.inner.list_transforms()
    }
    fn clone_pipeline(&mut self, py: Python<'_>, id: &str) -> PyResult<String> {
        self.inner.clone_pipeline(id).map_err(|e| error(py, e))
    }
    fn get_transform_vec(&self, py: Python<'_>, id: &str) -> PyResult<Vec<Instruction>> {
        self.inner
            .get_transform_vec(id)
            .map(|specs| specs.into_iter().map(Instruction::from_spec).collect())
            .map_err(|e| error(py, e))
    }
    #[pyo3(signature = (tasks, threads=0))]
    fn process_batch(
        &self,
        py: Python<'_>,
        tasks: Vec<(PyRef<'_, FilePath>, String, PyRef<'_, FilePath>)>,
        threads: u64,
    ) -> PyResult<Vec<Option<Py<PyAny>>>> {
        let tasks = tasks
            .into_iter()
            .map(|(input, pipeline_id, output)| portable::FileTask {
                input: input.inner.clone(),
                pipeline_id,
                output: output.inner.clone(),
            })
            .collect();
        let pool = portable::BatchPool::new(threads).map_err(|e| error(py, e))?;
        let results = py.detach(|| self.inner.process_batch_in_pool(&pool, tasks));
        Ok(results
            .into_iter()
            .map(|result| result.err().map(|e| error(py, e).into_value(py).into_any()))
            .collect())
    }
    fn get_text_transform_vec(&self, py: Python<'_>, id: &str) -> PyResult<Vec<String>> {
        self.inner
            .get_text_transform_vec(id)
            .map_err(|e| error(py, e))
    }
    fn process_all(&mut self, py: Python<'_>, id: &str, input: &str) -> PyResult<String> {
        py.detach(|| self.inner.process_all(id, input))
            .map_err(|e| error(py, e))
    }
    fn run_transform(&self, py: Python<'_>, id: &str, input: &str) -> PyResult<String> {
        py.detach(|| self.inner.run_transform(id, input))
            .map_err(|e| error(py, e))
    }
    fn process_single(
        &mut self,
        py: Python<'_>,
        instruction: &Instruction,
        input: &str,
    ) -> PyResult<String> {
        let spec = instruction.spec.clone();
        py.detach(|| self.inner.process_single(spec, input))
            .map_err(|e| error(py, e))
    }
    fn process_all_with_debug(
        &mut self,
        py: Python<'_>,
        id: &str,
        input: &str,
    ) -> PyResult<String> {
        py.detach(|| self.inner.process_all_with_debug(id, input))
            .map_err(|e| error(py, e))
    }
    fn process_single_with_debug(
        &mut self,
        py: Python<'_>,
        instruction: &Instruction,
        input: &str,
    ) -> PyResult<String> {
        let spec = instruction.spec.clone();
        py.detach(|| self.inner.process_single_with_debug(spec, input))
            .map_err(|e| error(py, e))
    }
    fn get_pipeline_from_file(&mut self, py: Python<'_>, path: &FilePath) -> PyResult<String> {
        py.detach(|| self.inner.get_pipeline_from_file(&path.inner))
            .map_err(|e| error(py, e))
    }
    fn write_pipeline_to_file(
        &mut self,
        py: Python<'_>,
        id: &str,
        path: &FilePath,
    ) -> PyResult<()> {
        py.detach(|| self.inner.write_pipeline_to_file(id, &path.inner))
            .map_err(|e| error(py, e))
    }
    fn read_from_bytecode_file(&mut self, py: Python<'_>, path: &FilePath) -> PyResult<String> {
        py.detach(|| self.inner.read_from_bytecode_file(&path.inner))
            .map_err(|e| error(py, e))
    }
    fn write_to_bytecode_file(
        &mut self,
        py: Python<'_>,
        id: &str,
        path: &FilePath,
    ) -> PyResult<()> {
        py.detach(|| self.inner.write_to_bytecode_file(id, &path.inner))
            .map_err(|e| error(py, e))
    }
    fn process_file(
        &mut self,
        py: Python<'_>,
        id: &str,
        input: &FilePath,
        output: &FilePath,
    ) -> PyResult<()> {
        py.detach(|| self.inner.process_file(id, &input.inner, &output.inner))
            .map_err(|e| error(py, e))
    }

    fn add_transform(
        &mut self,
        py: Python<'_>,
        instructions: Vec<PyRef<'_, Instruction>>,
    ) -> PyResult<String> {
        self.inner
            .add_transform(instructions.iter().map(|i| i.spec.clone()).collect())
            .map_err(|e| error(py, e))
    }
    fn show_transforms(&self) {
        self.inner.show_transforms();
    }
    fn process_batch_in_pool(
        &self,
        py: Python<'_>,
        pool: &BatchPool,
        tasks: Vec<(PyRef<'_, FilePath>, String, PyRef<'_, FilePath>)>,
    ) -> PyResult<Vec<Option<Py<PyAny>>>> {
        let tasks = tasks
            .into_iter()
            .map(|(input, pipeline_id, output)| portable::FileTask {
                input: input.inner.clone(),
                pipeline_id,
                output: output.inner.clone(),
            })
            .collect();
        let pool = pool.get()?;
        let results = py.detach(|| self.inner.process_batch_in_pool(pool, tasks));
        Ok(results
            .into_iter()
            .map(|r| r.err().map(|e| error(py, e).into_value(py).into_any()))
            .collect())
    }
    fn process_all_with_watchers(
        &mut self,
        py: Python<'_>,
        id: &str,
        input: &str,
        observers: &mut Observers,
        report: &FilePath,
    ) -> PyResult<String> {
        // Observers are thread-confined. Retain the GIL and both mutable borrow
        // guards throughout callbacks; re-entrant access fails before reaching Rust.
        self.inner
            .process_all_with_watchers(id, input, &mut observers.inner, &report.inner)
            .map_err(|e| error(py, e))
    }
    fn process_all_buffered(
        &mut self,
        py: Python<'_>,
        id: &str,
        input: &mut PortableBuffer,
    ) -> PyResult<PortableBuffer> {
        let input = input.take()?;
        py.detach(|| self.inner.process_all_buffered(id, input))
            .map(PortableBuffer::wrap)
            .map_err(|e| error(py, e))
    }
    fn process_single_buffered(
        &mut self,
        py: Python<'_>,
        instruction: &str,
        input: &mut PortableBuffer,
    ) -> PyResult<PortableBuffer> {
        let input = input.take()?;
        py.detach(|| self.inner.process_single_buffered(instruction, input))
            .map(PortableBuffer::wrap)
            .map_err(|e| error(py, e))
    }
    fn process_file_buffered(
        &mut self,
        py: Python<'_>,
        id: &str,
        input: &FilePath,
        options: &BufferOptions,
    ) -> PyResult<PortableBuffer> {
        py.detach(|| {
            self.inner
                .process_file_buffered(id, &input.inner, options.inner.clone())
        })
        .map(PortableBuffer::wrap)
        .map_err(|e| error(py, e))
    }
    fn process_batch_buffered(
        &self,
        py: Python<'_>,
        tasks: Vec<(String, PyRef<'_, FilePath>)>,
        options: &BufferOptions,
    ) -> PyResult<Vec<Py<PyAny>>> {
        let tasks = tasks
            .into_iter()
            .map(|(pipeline_id, input)| portable::BufferTask {
                pipeline_id,
                input: input.inner.clone(),
            })
            .collect();
        let results = py.detach(|| {
            self.inner
                .process_batch_buffered(tasks, options.inner.clone())
        });
        results
            .into_iter()
            .map(|r| match r {
                Ok(buffer) => Py::new(py, PortableBuffer::wrap(buffer)).map(Py::into_any),
                Err(e) => Ok(error(py, e).into_value(py).into_any()),
            })
            .collect()
    }
}
