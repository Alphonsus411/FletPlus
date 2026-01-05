use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

#[derive(FromPyObject, Debug)]
struct GridItemSpec {
    index: usize,
    span: Option<i64>,
    span_breakpoints: Option<HashMap<i64, i64>>,
    span_devices: Option<HashMap<String, i64>>,
    visible_devices: Option<Vec<String>>,
    hidden_devices: Option<Vec<String>>,
    min_width: Option<i64>,
    max_width: Option<i64>,
    has_responsive_style: Option<bool>,
}

fn sanitize_span(value: i64) -> i64 {
    value.clamp(1, 12)
}

fn resolve_span(item: &GridItemSpec, width: i64, columns: i64, device: &str) -> i64 {
    let normalized_device = device.to_lowercase();

    if let Some(ref span_devices) = item.span_devices {
        if let Some(raw_span) = span_devices.get(&normalized_device) {
            return sanitize_span(*raw_span);
        }
    }

    if let Some(ref breakpoints) = item.span_breakpoints {
        let mut selected: Option<i64> = None;
        for (bp, span) in breakpoints.iter() {
            if width >= *bp {
                selected = Some(*span);
            }
        }

        if let Some(span) = selected {
            return sanitize_span(span);
        }
    }

    if let Some(span) = item.span {
        return sanitize_span(span);
    }

    let cols = if columns <= 0 { 1 } else { columns };
    let default_span = 12 / cols;
    sanitize_span(default_span)
}

fn normalize_devices(devices: &Option<Vec<String>>) -> Option<Vec<String>> {
    devices.as_ref().map(|items| {
        items
            .iter()
            .filter_map(|item| {
                let normalized = item.trim().to_lowercase();
                if normalized.is_empty() {
                    None
                } else {
                    Some(normalized)
                }
            })
            .collect::<Vec<_>>()
    })
}

fn is_visible(item: &GridItemSpec, width: i64, device: &str) -> bool {
    if let Some(min_width) = item.min_width {
        if width < min_width {
            return false;
        }
    }

    if let Some(max_width) = item.max_width {
        if width > max_width {
            return false;
        }
    }

    let normalized_device = device.to_lowercase();
    if let Some(visible) = normalize_devices(&item.visible_devices) {
        return visible.iter().any(|name| *name == normalized_device);
    }

    if let Some(hidden) = normalize_devices(&item.hidden_devices) {
        if hidden.iter().any(|name| *name == normalized_device) {
            return false;
        }
    }

    true
}

#[pyfunction]
fn plan_items(
    py: Python<'_>,
    width: i64,
    columns: i64,
    device: &str,
    items: Vec<GridItemSpec>,
) -> PyResult<Vec<Py<PyDict>>> {
    if width < 0 {
        return Err(PyErr::new::<PyValueError, _>("El ancho no puede ser negativo"));
    }

    let mut result: Vec<Py<PyDict>> = Vec::new();

    for item in items.iter() {
        if !is_visible(item, width, device) {
            continue;
        }

        let col = resolve_span(item, width, columns, device);

        let dict = PyDict::new(py);
        dict.set_item("index", item.index)?;
        dict.set_item("col", col)?;
        dict.set_item("has_responsive_style", item.has_responsive_style.unwrap_or(false))?;
        result.push(dict.into());
    }

    Ok(result)
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(plan_items))?;
    Ok(())
}
