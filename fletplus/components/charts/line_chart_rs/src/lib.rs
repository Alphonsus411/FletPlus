use pyo3::prelude::*;

fn normalize_span(span: f32) -> f32 {
    if span == 0.0 {
        1.0
    } else {
        span
    }
}

#[pyfunction]
fn screen_points(
    data: Vec<(f32, f32)>,
    x_min: f32,
    x_max: f32,
    y_min: f32,
    y_max: f32,
    width: f32,
    height: f32,
    scale: f32,
) -> Vec<(f32, f32)> {
    let span_x = normalize_span((x_max - x_min) * scale);
    let span_y = normalize_span((y_max - y_min) * scale);

    data.into_iter()
        .map(|(x, y)| {
            let px = (x - x_min) / span_x * width;
            let py = height - (y - y_min) / span_y * height;
            (px, py)
        })
        .collect()
}

#[pyfunction]
fn nearest_point(points: Vec<(f32, f32)>, x: f32, y: f32) -> Option<(usize, f32)> {
    let mut best: Option<(usize, f32)> = None;

    for (idx, (px, py)) in points.into_iter().enumerate() {
        let dx = px - x;
        let dy = py - y;
        let dist = dx * dx + dy * dy;

        match best {
            None => best = Some((idx, dist)),
            Some((_, best_dist)) if dist < best_dist => best = Some((idx, dist)),
            _ => {}
        }
    }

    best
}

#[pyfunction]
fn line_segments(points: Vec<(f64, f64)>) -> Vec<(f64, f64, f64, f64)> {
    if points.len() < 2 {
        return Vec::new();
    }

    points
        .windows(2)
        .map(|pair| {
            let (x1, y1) = pair[0];
            let (x2, y2) = pair[1];
            (x1, y1, x2, y2)
        })
        .collect()
}

#[pymodule]
fn _native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(screen_points, m)?)?;
    m.add_function(wrap_pyfunction!(nearest_point, m)?)?;
    m.add_function(wrap_pyfunction!(line_segments, m)?)?;
    Ok(())
}
