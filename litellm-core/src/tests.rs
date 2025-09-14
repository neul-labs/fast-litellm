#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::Python;

    #[test]
    fn test_lite_llm_core_creation() {
        Python::with_gil(|py| {
            let module = pyo3::wrap_pymodule!(litellm_core)(py);
            assert!(module.getattr("LiteLLMCore").is_ok());
        });
    }

    #[test]
    fn test_deployment_creation() {
        Python::with_gil(|py| {
            let module = pyo3::wrap_pymodule!(litellm_core)(py);
            let deployment_class = module.getattr("Deployment").unwrap();
            
            let kwargs = vec![
                ("model_name", "test-model"),
                ("litellm_params", "{}"),
                ("model_info", "{}"),
            ];
            
            let result = deployment_class.call((), Some(kwargs.into_py_dict(py)));
            assert!(result.is_ok());
        });
    }

    #[test]
    fn test_health_check() {
        let result = health_check();
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), true);
    }
}