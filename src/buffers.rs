//! Owned buffers and synchronous Python binary stream invocation.
use super::*;
use crate::paths::FilePath;
use pyo3::{exceptions::PyValueError, types::PyBytes};

/// Portable spool settings; constructed by Python `BufferOptions(...)`.
#[pyclass(module = "textforge._native", frozen)]
pub(super) struct BufferOptions {
    pub(super) inner: portable::BufferOptions,
}
#[pymethods]
impl BufferOptions {
    #[new]
    fn new(memory_threshold: u64, spill_directory: &FilePath) -> Self {
        Self {
            inner: portable::BufferOptions {
                memory_threshold,
                spill_directory: spill_directory.inner.clone(),
            },
        }
    }
}

/// Owned UTF-8 buffer; Python: `PortableBuffer.from_text("é", options)`.
/// A consuming call invalidates every Python alias, including on failure.
#[pyclass(module = "textforge._native")]
pub(super) struct PortableBuffer {
    inner: Option<portable::PortableBuffer>,
}
impl PortableBuffer {
    pub(super) fn wrap(inner: portable::PortableBuffer) -> Self {
        Self { inner: Some(inner) }
    }
    pub(super) fn take(&mut self) -> PyResult<portable::PortableBuffer> {
        self.inner
            .take()
            .ok_or_else(|| PyValueError::new_err("buffer is closed or consumed"))
    }
    fn get(&self) -> PyResult<&portable::PortableBuffer> {
        self.inner
            .as_ref()
            .ok_or_else(|| PyValueError::new_err("buffer is closed or consumed"))
    }
    fn get_mut(&mut self) -> PyResult<&mut portable::PortableBuffer> {
        self.inner
            .as_mut()
            .ok_or_else(|| PyValueError::new_err("buffer is closed or consumed"))
    }
}
#[pymethods]
impl PortableBuffer {
    #[staticmethod]
    fn from_text(py: Python<'_>, text: &str, options: &BufferOptions) -> PyResult<Self> {
        py.detach(|| portable::PortableBuffer::from_text(text, options.inner.clone()))
            .map(Self::wrap)
            .map_err(|e| error(py, e))
    }
    #[staticmethod]
    fn from_file(py: Python<'_>, path: &FilePath, options: &BufferOptions) -> PyResult<Self> {
        py.detach(|| portable::PortableBuffer::from_file(&path.inner, options.inner.clone()))
            .map(Self::wrap)
            .map_err(|e| error(py, e))
    }
    #[staticmethod]
    fn from_reader(py: Python<'_>, reader: Py<PyAny>, options: &BufferOptions) -> PyResult<Self> {
        // The shared layer validates read sizes and UTF-8, including split code points.
        let read = move |maximum: u64| {
            Python::attach(|py| {
                reader
                    .bind(py)
                    .call_method1("read", (maximum,))
                    .and_then(|value| {
                        value
                            .cast::<PyBytes>()
                            .map(|b| b.as_bytes().to_vec())
                            .map_err(Into::into)
                    })
                    .map_err(|e: PyErr| e.to_string())
            })
        };
        portable::PortableBuffer::from_reader(Box::new(read), options.inner.clone())
            .map(Self::wrap)
            .map_err(|e| error(py, e))
    }
    fn len_bytes(&self) -> PyResult<u64> {
        Ok(self.get()?.len_bytes())
    }
    fn is_empty(&self) -> PyResult<bool> {
        Ok(self.get()?.is_empty())
    }
    fn is_spilled(&self) -> PyResult<bool> {
        Ok(self.get()?.is_spilled())
    }
    fn spill(&mut self, py: Python<'_>) -> PyResult<()> {
        let buffer = self.get_mut()?;
        py.detach(|| buffer.spill()).map_err(|e| error(py, e))
    }
    fn read_at<'py>(
        &mut self,
        py: Python<'py>,
        offset: u64,
        maximum: u64,
    ) -> PyResult<Bound<'py, PyBytes>> {
        let buffer = self.get_mut()?;
        py.detach(|| buffer.read_at(offset, maximum))
            .map(|b| PyBytes::new(py, &b))
            .map_err(|e| error(py, e))
    }
    fn copy_to(&mut self, py: Python<'_>, writer: Py<PyAny>) -> PyResult<u64> {
        let write = move |bytes: Vec<u8>| {
            Python::attach(|py| {
                let result = writer
                    .bind(py)
                    .call_method1("write", (PyBytes::new(py, &bytes),))?;
                if result.is_instance_of::<PyBool>() {
                    return Err(PyTypeError::new_err(
                        "write must return a byte count, not bool",
                    ));
                }
                result.extract::<u64>()
            })
            .map_err(|e: PyErr| e.to_string())
        };
        self.get_mut()?
            .copy_to(Box::new(write))
            .map_err(|e| error(py, e))
    }
    fn write_to_file(&mut self, py: Python<'_>, path: &FilePath) -> PyResult<u64> {
        let buffer = self.get_mut()?;
        py.detach(|| buffer.write_to_file(&path.inner))
            .map_err(|e| error(py, e))
    }
    #[pyo3(name = "into_string")]
    fn consume_text(&mut self, py: Python<'_>) -> PyResult<String> {
        let buffer = self.take()?;
        py.detach(|| buffer.into_string()).map_err(|e| error(py, e))
    }
    fn close(&mut self) {
        self.inner = None;
    }
    #[getter]
    fn closed(&self) -> bool {
        self.inner.is_none()
    }
}
