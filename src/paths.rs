//! Owned portable paths, capability discovery, and reusable worker pools.
use super::*;
use pyo3::exceptions::PyValueError;

/// Lossless native path; Python: `FilePath.from_native_bytes(b"input")` on Unix.
#[pyclass(module = "textforge", frozen)]
pub(super) struct FilePath {
    pub(super) inner: portable::FilePath,
}
#[pymethods]
impl FilePath {
    #[staticmethod]
    fn from_text(path: String) -> Self {
        Self {
            inner: portable::FilePath::from_text(path),
        }
    }
    #[staticmethod]
    fn from_native_bytes(py: Python<'_>, bytes: Vec<u8>) -> PyResult<Self> {
        portable::FilePath::from_native_bytes(bytes)
            .map(|inner| Self { inner })
            .map_err(|e| error(py, e))
    }
    #[staticmethod]
    fn from_windows_wide(py: Python<'_>, wide: Vec<u16>) -> PyResult<Self> {
        portable::FilePath::from_windows_wide(wide)
            .map(|inner| Self { inner })
            .map_err(|e| error(py, e))
    }
    fn to_text(&self) -> Option<String> {
        self.inner.to_text()
    }
    fn to_native_bytes<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        self.inner
            .to_native_bytes()
            .map(|bytes| pyo3::types::PyBytes::new(py, &bytes))
            .map_err(|e| error(py, e))
    }
    fn to_windows_wide(&self, py: Python<'_>) -> PyResult<Vec<u16>> {
        self.inner.to_windows_wide().map_err(|e| error(py, e))
    }
}

/// Build capabilities; Python: `features().watchers`.
#[pyclass(module = "textforge", frozen, get_all)]
pub(super) struct Features {
    bytecode: bool,
    watchers: bool,
    buffered: bool,
}
#[pyfunction]
pub(super) fn features() -> Features {
    let f = portable::features();
    Features {
        bytecode: f.bytecode,
        watchers: f.watchers,
        buffered: f.buffered,
    }
}

/// Caller-owned reusable pool; Python: `BatchPool(2)`; `close()` releases workers.
#[pyclass(module = "textforge._native")]
pub(super) struct BatchPool {
    inner: Option<portable::BatchPool>,
}
impl BatchPool {
    pub(super) fn get(&self) -> PyResult<&portable::BatchPool> {
        self.inner
            .as_ref()
            .ok_or_else(|| PyValueError::new_err("batch pool is closed"))
    }
}
#[pymethods]
impl BatchPool {
    #[new]
    #[pyo3(signature = (threads=0))]
    fn new(py: Python<'_>, threads: u64) -> PyResult<Self> {
        py.detach(|| portable::BatchPool::new(threads))
            .map(|inner| Self { inner: Some(inner) })
            .map_err(|e| error(py, e))
    }
    fn close(&mut self) {
        self.inner = None;
    }
    #[getter]
    fn closed(&self) -> bool {
        self.inner.is_none()
    }
}
