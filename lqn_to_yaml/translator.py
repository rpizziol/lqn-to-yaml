from .parser import LQNModel, Task

# A configurable default image
DEFAULT_IMAGE = "rpizziol/generic-microservice-tester:latest"

def _build_outbound_calls_env(task: Task, all_tasks: dict) -> str:
    """Builds the OUTBOUND_CALLS environment variable string."""
    call_strings = []
    
    # Find the main activity (assuming the one with service time > 0.0001)
    main_activity = next((act for act in task.activities.values() if act.service_time > 0.0001), None)
    if not main_activity or not main_activity.calls:
        return ""

    for call in main_activity.calls:
        call_type = "SYNC" if call.call_type == 'y' else "ASYNC"
        
        # Find the target task name from its entry name
        target_task_name = ""
        for t in all_tasks.values():
            if t.entry_name == call.target_entry:
                target_task_name = t.name
                break
        
        if not target_task_name:
            continue

        target_svc_name = f"{target_task_name.lower()}-svc"
        
        # For now, we assume num_calls=1 and don't include probability
        # Format: TYPE:TARGET:PROB
        call_strings.append(f"{call_type}:{target_svc_name}:{call.probability}")

    return ",".join(call_strings)


def translate_to_k8s(model: LQNModel, image_name: str = DEFAULT_IMAGE) -> list:
    """
    Translates an LQNModel object into a list of Kubernetes resource definitions.
    """
    k8s_objects = []
    
    for task_name, task in model.tasks.items():
        app_label = task_name.lower()
        deployment_name = f"{app_label}-deployment"
        service_name = f"{app_label}-svc"
        
        main_activity = next((act for act in task.activities.values() if act.service_time > 0.0001), None)
        service_time_val = str(main_activity.service_time) if main_activity else "0.1"

        # --- Define Deployment ---
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": deployment_name},
            "spec": {
                "replicas": task.multiplicity if task.name == 'Task0' else 1, # Example logic
                "selector": {"matchLabels": {"app": app_label}},
                "template": {
                    "metadata": {"labels": {"app": app_label}},
                    "spec": {
                        "containers": [{
                            "name": "app",
                            "image": image_name,
                            "ports": [{"containerPort": 8080}],
                            "env": [
                                {"name": "SERVICE_NAME", "value": service_name},
                                {"name": "SERVICE_TIME_SECONDS", "value": service_time_val},
                                {"name": "OUTBOUND_CALLS", "value": _build_outbound_calls_env(task, model.tasks)},
                                # Default Gunicorn settings, can be mapped from processor later
                                {"name": "GUNICORN_WORKERS", "value": "1"}, 
                                {"name": "GUNICORN_THREADS", "value": "4"},
                            ]
                        }]
                    }
                }
            }
        }
        k8s_objects.append(deployment)

        # --- Define Service ---
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": service_name},
            "spec": {
                "selector": {"app": app_label},
                "ports": [{
                    "name": "http",
                    "protocol": "TCP",
                    "port": 80,
                    "targetPort": 8080
                }]
            }
        }
        k8s_objects.append(service)

    return k8s_objects
