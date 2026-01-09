use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};
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

fn get_attr_or_key<'py>(item: &'py PyAny, name: &str) -> PyResult<Option<&'py PyAny>> {
    if let Ok(value) = item.getattr(name) {
        if value.is_none() {
            return Ok(None);
        }
        return Ok(Some(value));
    }

    if let Ok(dict) = item.downcast::<PyDict>() {
        if let Some(value) = dict.get_item(name) {
            if value.is_none() {
                return Ok(None);
            }
            return Ok(Some(value));
        }
    }

    Ok(None)
}

fn extract_breakpoints(value: &PyAny) -> PyResult<HashMap<i64, i64>> {
    if let Ok(mapping) = value.extract::<HashMap<i64, i64>>() {
        return Ok(mapping);
    }

    let dict = value
        .downcast::<PyDict>()
        .map_err(|_| PyErr::new::<PyValueError, _>("Breakpoints inválidos"))?;
    let mut map = HashMap::new();
    for (key, val) in dict.iter() {
        let parsed_key = if let Ok(num) = key.extract::<i64>() {
            num
        } else {
            let text = key
                .extract::<String>()
                .map_err(|_| PyErr::new::<PyValueError, _>("Breakpoint inválido"))?;
            text.parse::<i64>()
                .map_err(|_| PyErr::new::<PyValueError, _>("Breakpoint inválido"))?
        };
        let parsed_value = val.extract::<i64>()?;
        map.insert(parsed_key, parsed_value);
    }
    Ok(map)
}

fn extract_span_devices(value: &PyAny) -> PyResult<HashMap<String, i64>> {
    if let Ok(mapping) = value.extract::<HashMap<String, i64>>() {
        return Ok(mapping);
    }

    let dict = value
        .downcast::<PyDict>()
        .map_err(|_| PyErr::new::<PyValueError, _>("Span por dispositivo inválido"))?;
    let mut map = HashMap::new();
    for (key, val) in dict.iter() {
        let parsed_key = key
            .extract::<String>()
            .map_err(|_| PyErr::new::<PyValueError, _>("Dispositivo inválido"))?;
        let parsed_value = val.extract::<i64>()?;
        map.insert(parsed_key, parsed_value);
    }
    Ok(map)
}

fn extract_device_list(value: &PyAny) -> PyResult<Option<Vec<String>>> {
    if value.is_none() {
        return Ok(None);
    }

    if let Ok(text) = value.extract::<String>() {
        return Ok(Some(vec![text]));
    }

    if let Ok(list) = value.extract::<Vec<String>>() {
        return Ok(Some(list));
    }

    Err(PyErr::new::<PyValueError, _>(
        "Lista de dispositivos inválida",
    ))
}

fn build_item_spec_from_object(item: &PyAny, index: usize) -> PyResult<GridItemSpec> {
    let span = get_attr_or_key(item, "span")?.map(|value| value.extract::<i64>()).transpose()?;
    let span_breakpoints = if let Some(value) = get_attr_or_key(item, "span_breakpoints")? {
        Some(extract_breakpoints(value)?)
    } else {
        None
    };
    let span_devices = if let Some(value) = get_attr_or_key(item, "span_devices")? {
        Some(extract_span_devices(value)?)
    } else {
        None
    };
    let visible_devices = if let Some(value) = get_attr_or_key(item, "visible_devices")? {
        extract_device_list(value)?
    } else {
        None
    };
    let hidden_devices = if let Some(value) = get_attr_or_key(item, "hidden_devices")? {
        extract_device_list(value)?
    } else {
        None
    };
    let min_width = get_attr_or_key(item, "min_width")?
        .map(|value| value.extract::<i64>())
        .transpose()?;
    let max_width = get_attr_or_key(item, "max_width")?
        .map(|value| value.extract::<i64>())
        .transpose()?;
    let has_responsive_style = get_attr_or_key(item, "responsive_style")?.is_some();

    Ok(GridItemSpec {
        index,
        span,
        span_breakpoints,
        span_devices,
        visible_devices,
        hidden_devices,
        min_width,
        max_width,
        has_responsive_style: Some(has_responsive_style),
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

#[pyfunction]
fn plan_items_from_objects(
    py: Python<'_>,
    width: i64,
    columns: i64,
    device: &str,
    items: Vec<PyObject>,
) -> PyResult<Vec<Py<PyDict>>> {
    if width < 0 {
        return Err(PyErr::new::<PyValueError, _>("El ancho no puede ser negativo"));
    }

    let mut result: Vec<Py<PyDict>> = Vec::new();

    for (index, item) in items.iter().enumerate() {
        let spec = build_item_spec_from_object(item.as_ref(py), index)?;
        if !is_visible(&spec, width, device) {
            continue;
        }

        let col = resolve_span(&spec, width, columns, device);

        let dict = PyDict::new(py);
        dict.set_item("index", spec.index)?;
        dict.set_item("col", col)?;
        dict.set_item(
            "has_responsive_style",
            spec.has_responsive_style.unwrap_or(false),
        )?;
        result.push(dict.into());
    }

    Ok(result)
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(plan_items))?;
    m.add_wrapped(wrap_pyfunction!(plan_items_from_objects))?;
    Ok(())
}
