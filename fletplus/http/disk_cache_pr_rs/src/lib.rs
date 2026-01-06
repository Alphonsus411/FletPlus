use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyIterator, PyString};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;
use std::time::{Duration, SystemTime};

fn bytes_from_any(py: Python<'_>, obj: &PyAny) -> PyResult<Vec<u8>> {
    if obj.is_none() {
        return Ok(Vec::new());
    }

    if let Ok(bytes) = obj.downcast::<PyBytes>() {
        return Ok(bytes.as_bytes().to_vec());
    }

    if let Ok(text) = obj.downcast::<PyString>() {
        return Ok(text.to_str()?.as_bytes().to_vec());
    }

    let builtins = py.import("builtins")?;
    let bytes_ctor = builtins.getattr("bytes")?;
    let converted = bytes_ctor.call1((obj,))?;
    let bytes = converted.downcast::<PyBytes>()?;
    Ok(bytes.as_bytes().to_vec())
}

#[pyfunction]
fn build_key(py: Python<'_>, request: &PyAny) -> PyResult<String> {
    let mut hasher = Sha256::new();

    let method: String = request.getattr("method")?.extract()?;
    hasher.update(method.as_bytes());
    hasher.update(b"\n");

    let url_obj = request.getattr("url")?;
    let url_str = url_obj.str()?.to_str()?.to_owned();
    hasher.update(url_str.as_bytes());
    hasher.update(b"\n");

    let headers = request.getattr("headers")?;
    let raw = headers.getattr("raw")?;
    let iter: &PyIterator = raw.iter()?;
    let mut header_pairs: Vec<(Vec<u8>, Vec<u8>)> = Vec::new();
    for item in iter {
        let tuple: (Vec<u8>, Vec<u8>) = item?.extract()?;
        header_pairs.push(tuple);
    }
    header_pairs.sort_by(|a, b| a.0.cmp(&b.0));
    for (name, value) in header_pairs {
        hasher.update(&name);
        hasher.update(b":");
        hasher.update(&value);
        hasher.update(b"\n");
    }

    let content = request.getattr("content")?;
    let body = bytes_from_any(py, content)?;
    hasher.update(&body);

    Ok(format!("{:x}", hasher.finalize()))
}

fn cutoff_time(max_age: Option<f64>) -> Option<SystemTime> {
    max_age.map(|age| SystemTime::now() - Duration::from_secs_f64(age))
}

#[pyfunction]
fn cleanup(directory: &str, max_entries: usize, max_age: Option<f64>) -> PyResult<usize> {
    let dir = Path::new(directory);
    if !dir.exists() {
        return Ok(0);
    }

    let mut entries: Vec<(std::path::PathBuf, SystemTime)> = Vec::new();
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.extension().and_then(|ext| ext.to_str()) != Some("json") {
            continue;
        }
        let modified = entry
            .metadata()
            .and_then(|m| m.modified())
            .unwrap_or(SystemTime::UNIX_EPOCH);
        entries.push((path, modified));
    }

    entries.sort_by(|a, b| b.1.cmp(&a.1));
    let cutoff = cutoff_time(max_age);
    let mut kept = 0usize;
    let mut removed = 0usize;

    for (path, modified) in entries {
        if let Some(limit) = cutoff {
            if modified < limit {
                let _ = fs::remove_file(&path);
                removed += 1;
                continue;
            }
        }
        kept += 1;
        if kept > max_entries {
            let _ = fs::remove_file(&path);
            removed += 1;
        }
    }

    Ok(removed)
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(build_key, m)?)?;
    m.add_function(wrap_pyfunction!(cleanup, m)?)?;
    Ok(())
}
