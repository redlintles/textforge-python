//! Thread-confined watcher callbacks with Python garbage-collector visibility.
use super::*;
use crate::paths::FilePath;
use pyo3::{PyTraverseError, PyVisit};
use std::{collections::HashMap, rc::Rc};

/// Owned observation; Python: `Observation("é", "", None, "atb")`.
#[pyclass(module = "textforge", frozen, get_all)]
#[derive(Clone)]
pub(super) struct Observation {
    current: String,
    before: String,
    after: Option<String>,
    instruction: String,
}
impl From<portable::Observation> for Observation {
    fn from(o: portable::Observation) -> Self {
        Self {
            current: o.current,
            before: o.before,
            after: o.after,
            instruction: o.instruction,
        }
    }
}
#[pymethods]
impl Observation {
    #[new]
    fn new(current: String, before: String, after: Option<String>, instruction: String) -> Self {
        Self {
            current,
            before,
            after,
            instruction,
        }
    }
}

/// Watcher registrations; Python: `Observers().set_builtin("size", "word_count")`.
/// Callbacks are strongly retained until replacement, clear, or collection.
#[pyclass(module = "textforge._native", unsendable)]
#[derive(Default)]
pub(super) struct Observers {
    pub(super) inner: portable::Observers,
    // One Python reference per callback, shared with its Rust closure through Rc.
    // Traversal must report that reference exactly once for cycle collection.
    callbacks: HashMap<String, Rc<Py<PyAny>>>,
}
#[pymethods]
impl Observers {
    #[new]
    fn new() -> Self {
        Self::default()
    }
    fn set(&mut self, name: String, callback: Py<PyAny>) {
        let callback = Rc::new(callback);
        let retained = Rc::clone(&callback);
        self.inner.set(
            name.clone(),
            Box::new(move |o: portable::Observation| {
                Python::attach(|py| {
                    retained
                        .bind(py)
                        .call1((Observation::from(o),))?
                        .extract::<String>()
                })
                .map_err(|e: PyErr| e.to_string())
            }),
        );
        self.callbacks.insert(name, callback);
    }
    fn set_builtin(&mut self, py: Python<'_>, name: String, metric: &str) -> PyResult<()> {
        self.inner
            .set_builtin(name.clone(), metric)
            .map_err(|e| error(py, e))?;
        self.callbacks.remove(&name);
        Ok(())
    }
    #[staticmethod]
    fn builtin_names() -> Vec<String> {
        portable::Observers::builtin_names()
    }
    fn schedule_all(&mut self, py: Python<'_>, name: &str) -> PyResult<()> {
        self.inner.schedule_all(name).map_err(|e| error(py, e))
    }
    fn reset(&mut self) {
        self.inner.reset();
    }
    fn run(&mut self, py: Python<'_>, observation: &Observation) -> PyResult<()> {
        self.inner
            .run(portable::Observation {
                current: observation.current.clone(),
                before: observation.before.clone(),
                after: observation.after.clone(),
                instruction: observation.instruction.clone(),
            })
            .map_err(|e| error(py, e))
    }
    fn write_report(&self, py: Python<'_>, path: &FilePath) -> PyResult<()> {
        self.inner
            .write_report(&path.inner)
            .map_err(|e| error(py, e))
    }
    fn clear(&mut self) {
        self.inner = portable::Observers::new();
        self.callbacks.clear();
    }
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        for callback in self.callbacks.values() {
            visit.call(callback.as_ref())?;
        }
        Ok(())
    }
    fn __clear__(&mut self) {
        self.clear();
    }
}
