import argparse
import os
from .parser import parse_lqn_file
from .translator import translate_to_k8s
# Ho rimosso l'import di 'save_as_yaml' da qui per evitare il circular import

def main():
    # L'import viene spostato qui. Verrà eseguito solo quando la funzione main()
    # viene chiamata, rompendo il ciclo di dipendenze.
    from .generator import save_as_yaml

    parser = argparse.ArgumentParser(
        description="Translate LQN performance models to Kubernetes YAML manifests."
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to the input .lqn file."
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Path for the output .yaml file."
    )
    parser.add_argument(
        "--image",
        default="rpizziol/generic-microservice-tester:latest",
        help="The Docker image to use for the microservices."
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found at {args.input}")
        return

    # 1. Parse the LQN file
    print(f"Parsing LQN model from {args.input}...")
    lqn_model = parse_lqn_file(args.input)

    # 2. Translate the model to K8s objects
    print("Translating model to Kubernetes objects...")
    k8s_objects = translate_to_k8s(lqn_model, args.image)

    # 3. Generate the final YAML file
    print(f"Generating YAML manifest at {args.output}...")
    save_as_yaml(k8s_objects, args.output)

if __name__ == '__main__':
    main()