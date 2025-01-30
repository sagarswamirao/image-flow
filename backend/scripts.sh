# install keda components
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace

kubectl apply -f pubsub-secret.yaml
kubectl apply -f image_handler_deployment.yaml
kubectl apply -f image_handler_service.yaml
kubectl apply -f interaction_manager_deployment.yaml
kubectl apply -f interaction_manager_service.yaml
kubectl apply -f image_processor_deployment.yaml
