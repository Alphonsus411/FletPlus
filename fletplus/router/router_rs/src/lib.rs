use std::collections::HashMap;

use pyo3::prelude::*;
use pyo3::types::PyList;

fn normalize_path_internal(path: &str) -> Vec<String> {
    let cleaned = path.trim();
    if cleaned.is_empty() || cleaned == "/" {
        return Vec::new();
    }

    let mut trimmed = cleaned;
    if let Some(stripped) = cleaned.strip_prefix('/') {
        trimmed = stripped;
    }
    if let Some(stripped) = trimmed.strip_suffix('/') {
        trimmed = stripped;
    }

    trimmed
        .split('/')
        .filter(|segment| !segment.is_empty())
        .map(|segment| segment.to_string())
        .collect()
}

#[pyfunction(name = "_normalize_path")]
fn normalize_path(path: &str) -> PyResult<Vec<String>> {
    Ok(normalize_path_internal(path))
}

#[pyfunction(name = "_normalize_path_string")]
fn normalize_path_string(path: &str) -> PyResult<String> {
    if path.is_empty() {
        return Ok("/".to_string());
    }
    let segments = normalize_path_internal(path);
    Ok(format!("/{}", segments.join("/")))
}

#[pyfunction(name = "_parse_segment")]
fn parse_segment(segment: &str) -> PyResult<(bool, Option<String>)> {
    if segment.starts_with('<') && segment.ends_with('>') && segment.len() > 2 {
        Ok((true, Some(segment[1..segment.len() - 1].to_string())))
    } else {
        Ok((false, None))
    }
}

#[pyfunction(name = "_join_paths")]
fn join_paths(base: &str, segment: &str) -> PyResult<String> {
    let mut cleaned_base = base.trim_end_matches('/').to_string();
    if cleaned_base.is_empty() {
        cleaned_base.push('/');
    }

    if segment.starts_with('/') {
        return normalize_path_string(segment);
    }

    if cleaned_base == "/" {
        Ok(format!("/{}", segment))
    } else {
        Ok(format!("{}/{}", cleaned_base, segment))
    }
}

fn has_view_builder(node: &PyAny) -> PyResult<bool> {
    Ok(!node.getattr("view_builder")?.is_none())
}

fn collect_children<'a>(node: &'a PyAny) -> PyResult<(Vec<&'a PyAny>, Vec<&'a PyAny>)> {
    let children: &PyList = node.getattr("children")?.downcast()?;
    let mut static_children: Vec<&PyAny> = Vec::new();
    let mut dynamic_children: Vec<&PyAny> = Vec::new();

    for child in children.iter() {
        let is_dynamic = child.getattr("dynamic")?.extract::<bool>()?;
        if is_dynamic {
            dynamic_children.push(child);
        } else {
            static_children.push(child);
        }
    }

    Ok((static_children, dynamic_children))
}

fn collect_result(
    stack_nodes: &[Option<PyObject>],
    log_lengths: &[usize],
    param_log: &[(String, String)],
    depth: usize,
    results: &mut Vec<Vec<(PyObject, HashMap<String, String>)>>,
) {
    let mut current_params: HashMap<String, String> = HashMap::new();
    let mut applied = 0_usize;
    let mut path: Vec<(PyObject, HashMap<String, String>)> = Vec::with_capacity(depth + 1);

    for level in 0..=depth {
        let target_len = log_lengths[level];
        while applied < target_len {
            let (key, value) = &param_log[applied];
            current_params.insert(key.clone(), value.clone());
            applied += 1;
        }

        if let Some(node) = &stack_nodes[level] {
            path.push((node.clone(), current_params.clone()));
        }
    }

    results.push(path);
}

fn dfs_match(
    py: Python<'_>,
    node: &PyAny,
    segments: &[String],
    index: usize,
    params: &mut HashMap<String, String>,
    param_log: &mut Vec<(String, String)>,
    stack_nodes: &mut Vec<Option<PyObject>>,
    log_lengths: &mut Vec<usize>,
    results: &mut Vec<Vec<(PyObject, HashMap<String, String>)>>,
) -> PyResult<()> {
    if index == segments.len() {
        stack_nodes[index] = Some(node.into_py(py));
        log_lengths[index] = param_log.len();
        if has_view_builder(node)? {
            collect_result(stack_nodes, log_lengths, param_log, index, results);
        }
        return Ok(());
    }

    let segment = &segments[index];
    let (static_children, dynamic_children) = collect_children(node)?;

    for child in static_children {
        let child_segment: String = child.getattr("segment")?.extract()?;
        if child_segment == *segment {
            stack_nodes[index] = Some(child.into_py(py));
            log_lengths[index] = param_log.len();
            dfs_match(
                py,
                child,
                segments,
                index + 1,
                params,
                param_log,
                stack_nodes,
                log_lengths,
                results,
            )?;
        }
    }

    for child in dynamic_children {
        let parameter_name: Option<String> = child.getattr("parameter_name")?.extract()?;
        let key = parameter_name.unwrap_or_else(|| "param".to_string());
        params.insert(key.clone(), segment.clone());
        param_log.push((key.clone(), segment.clone()));
        stack_nodes[index] = Some(child.into_py(py));
        log_lengths[index] = param_log.len();
        dfs_match(
            py,
            child,
            segments,
            index + 1,
            params,
            param_log,
            stack_nodes,
            log_lengths,
            results,
        )?;
        params.remove(&key);
        param_log.pop();
    }

    Ok(())
}

#[pyfunction(name = "_dfs_match")]
fn dfs_match_public(
    py: Python<'_>,
    node: &PyAny,
    segments: Vec<String>,
    index: usize,
    params: HashMap<String, String>,
    stack: Vec<Option<(PyObject, HashMap<String, String>)>>,
    results: &PyAny,
) -> PyResult<()> {
    let mut params = params;
    let mut stack_nodes: Vec<Option<PyObject>> = vec![None; stack.len()];
    let mut log_lengths: Vec<usize> = vec![0; stack.len()];
    let mut param_log: Vec<(String, String)> = Vec::new();
    let mut collected: Vec<Vec<(PyObject, HashMap<String, String>)>> = Vec::new();

    dfs_match(
        py,
        node,
        &segments,
        index,
        &mut params,
        &mut param_log,
        &mut stack_nodes,
        &mut log_lengths,
        &mut collected,
    )?;
    for path in collected {
        results.call_method1("append", (path,))?;
    }
    Ok(())
}

#[pyfunction(name = "_match")]
fn match_routes(
    py: Python<'_>,
    root: &PyAny,
    path: &str,
) -> PyResult<Vec<Vec<(PyObject, HashMap<String, String>)>>> {
    let segments = normalize_path_internal(path);
    let mut results: Vec<Vec<(PyObject, HashMap<String, String>)>> = Vec::new();

    if segments.is_empty() {
        if has_view_builder(root)? {
            results.push(vec![(root.into_py(py), HashMap::new())]);
        }
        return Ok(results);
    }

    let mut params: HashMap<String, String> = HashMap::new();
    let mut param_log: Vec<(String, String)> = Vec::new();
    let mut stack_nodes: Vec<Option<PyObject>> = vec![None; segments.len() + 1];
    let mut log_lengths: Vec<usize> = vec![0; segments.len() + 1];
    dfs_match(
        py,
        root,
        &segments,
        0,
        &mut params,
        &mut param_log,
        &mut stack_nodes,
        &mut log_lengths,
        &mut results,
    )?;
    Ok(results)
}

#[pymodule]
fn _native(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(normalize_path, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_path_string, m)?)?;
    m.add_function(wrap_pyfunction!(parse_segment, m)?)?;
    m.add_function(wrap_pyfunction!(join_paths, m)?)?;
    m.add_function(wrap_pyfunction!(dfs_match_public, m)?)?;
    m.add_function(wrap_pyfunction!(match_routes, m)?)?;
    Ok(())
}
