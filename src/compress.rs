use crate::engines::compression::{
    diff_compressor::{DiffCompressor, DiffCompressorConfig},
    log_compressor::{LogCompressor, LogCompressorConfig},
    smart_crusher::{SmartCrusher, SmartCrusherConfig},
    text_crusher::{TextCrusher, TextCrusherConfig},
};
use pyo3::prelude::*;

#[pyclass(name = "CompressionResult")]
pub struct PyCompressionResult {
    #[pyo3(get)]
    pub compressed: String,
    #[pyo3(get)]
    pub original_size: usize,
    #[pyo3(get)]
    pub compressed_size: usize,
    #[pyo3(get)]
    pub strategy: String,
}

#[pyclass(name = "SmartCrusher")]
pub struct PySmartCrusher {
    inner: SmartCrusher,
}

#[pymethods]
impl PySmartCrusher {
    #[new]
    fn new() -> Self {
        PySmartCrusher {
            inner: SmartCrusher::new(SmartCrusherConfig::default()),
        }
    }

    fn crush(&self, content: &str, query: &str, target_ratio: f64) -> PyCompressionResult {
        let res = self.inner.crush(content, query, target_ratio);
        PyCompressionResult {
            original_size: res.original.len(),
            compressed_size: res.compressed.len(),
            compressed: res.compressed,
            strategy: res.strategy,
        }
    }
}

#[pyclass(name = "DiffCompressor")]
pub struct PyDiffCompressor {
    inner: DiffCompressor,
}

#[pymethods]
impl PyDiffCompressor {
    #[new]
    fn new() -> Self {
        PyDiffCompressor {
            inner: DiffCompressor::new(DiffCompressorConfig::default()),
        }
    }

    fn compress(&self, content: &str, query: &str) -> PyCompressionResult {
        let res = self.inner.compress(content, query);
        PyCompressionResult {
            original_size: content.len(),
            compressed_size: res.compressed.len(),
            compressed: res.compressed,
            strategy: "diff".to_string(),
        }
    }
}

#[pyclass(name = "LogCompressor")]
pub struct PyLogCompressor {
    inner: LogCompressor,
}

#[pymethods]
impl PyLogCompressor {
    #[new]
    fn new() -> Self {
        PyLogCompressor {
            inner: LogCompressor::new(LogCompressorConfig::default()),
        }
    }

    fn compress(&self, content: &str, target_ratio: f64) -> PyCompressionResult {
        let (res, _) = self.inner.compress(content, target_ratio);
        PyCompressionResult {
            original_size: res.original.len(),
            compressed_size: res.compressed.len(),
            compressed: res.compressed,
            strategy: "log".to_string(),
        }
    }
}

#[pyclass(name = "TextCrusher")]
pub struct PyTextCrusher {
    inner: TextCrusher,
}

#[pymethods]
impl PyTextCrusher {
    #[new]
    fn new() -> Self {
        PyTextCrusher {
            inner: TextCrusher::new(TextCrusherConfig::default()),
        }
    }

    fn compress(
        &self,
        content: &str,
        query: &str,
        target_ratio: Option<f64>,
    ) -> PyCompressionResult {
        let res = self.inner.compress(content, query, target_ratio);
        PyCompressionResult {
            original_size: content.len(),
            compressed_size: res.compressed.len(),
            compressed: res.compressed,
            strategy: "text".to_string(),
        }
    }
}

#[pyfunction]
pub fn route_and_compress(content: &str) -> String {
    crate::engines::compression::route_and_compress(content)
}

pub fn register_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyCompressionResult>()?;
    m.add_class::<PySmartCrusher>()?;
    m.add_class::<PyDiffCompressor>()?;
    m.add_class::<PyLogCompressor>()?;
    m.add_class::<PyTextCrusher>()?;
    m.add_function(wrap_pyfunction!(route_and_compress, m)?)?;
    Ok(())
}
