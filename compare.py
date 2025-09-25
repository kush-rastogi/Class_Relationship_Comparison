import json
import os
import csv
from collections import defaultdict


def load_model_from_json(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    classes = set(data.get("classes", []))
    relationships = set()
    for rel in data.get("relationships", []):
        relationships.add((rel["from"], rel["to"], rel["label"]))
    return {"classes": classes, "relationships": relationships}


def compare_models(models):
    comparison = {}
    all_classes = set()
    all_relationships = set()

    for model_name, model_data in models.items():
        all_classes.update(model_data["classes"])
        all_relationships.update(model_data["relationships"])

    class_presence = defaultdict(list)
    for cls in all_classes:
        for model_name, model_data in models.items():
            if cls in model_data["classes"]:
                class_presence[cls].append(model_name)

    relationship_presence = defaultdict(list)
    for rel in all_relationships:
        for model_name, model_data in models.items():
            if rel in model_data["relationships"]:
                relationship_presence[rel].append(model_name)

    comparison["classes"] = class_presence
    comparison["relationships"] = relationship_presence

    return comparison, all_classes, all_relationships


def evaluate_models(models, all_classes, all_relationships, comparison):
    scores = {}
    metrics = {}

    for model_name, model_data in models.items():
        # Recall for Classes
        recall_classes = len(model_data["classes"]) / len(all_classes) if all_classes else 0
        # Precision for Classes (Overlap with other models)
        class_overlap_count = sum([1 for cls in model_data["classes"] if len(comparison["classes"][cls]) > 1])
        precision_classes = class_overlap_count / len(model_data["classes"]) if model_data["classes"] else 0

        # Recall for Relationships
        recall_rels = len(model_data["relationships"]) / len(all_relationships) if all_relationships else 0
        # Precision for Relationships
        rel_overlap_count = sum([1 for rel in model_data["relationships"] if len(comparison["relationships"][rel]) > 1])
        precision_rels = rel_overlap_count / len(model_data["relationships"]) if model_data["relationships"] else 0

        # Overlap score
        overlap_score = (class_overlap_count + rel_overlap_count) / (len(model_data["classes"]) + len(model_data["relationships"])) if (model_data["classes"] or model_data["relationships"]) else 0

        # Weighted total score (simple sum here for demonstration)
        total_score = (
            0.25 * recall_classes +
            0.25 * precision_classes +
            0.25 * recall_rels +
            0.15 * precision_rels +
            0.10 * overlap_score
        )

        scores[model_name] = total_score
        metrics[model_name] = {
            "recall_classes": recall_classes,
            "precision_classes": precision_classes,
            "recall_relationships": recall_rels,
            "precision_relationships": precision_rels,
            "overlap_score": overlap_score,
            "total_score": total_score
        }

    return scores, metrics


def save_results_to_csv(comparison, scores, metrics, output_file="uml_comparison_results.csv"):
    with open(output_file, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(["Class Comparison"])
        writer.writerow(["Class", "Present In Models"])
        for cls, model_list in comparison["classes"].items():
            writer.writerow([cls, ", ".join(model_list)])

        writer.writerow([])

        writer.writerow(["Relationship Comparison"])
        writer.writerow(["From", "To", "Label", "Present In Models"])
        for rel, model_list in comparison["relationships"].items():
            writer.writerow([rel[0], rel[1], rel[2], ", ".join(model_list)])

        writer.writerow([])

        writer.writerow(["Model Metrics"])
        writer.writerow(["Model", "Recall Classes", "Precision Classes", "Recall Relationships", "Precision Relationships", "Overlap Score", "Total Score"])
        for model, metric in metrics.items():
            writer.writerow([
                model,
                f"{metric['recall_classes']:.3f}",
                f"{metric['precision_classes']:.3f}",
                f"{metric['recall_relationships']:.3f}",
                f"{metric['precision_relationships']:.3f}",
                f"{metric['overlap_score']:.3f}",
                f"{metric['total_score']:.3f}"
            ])

        writer.writerow([])
        writer.writerow(["Best Model", max(scores, key=scores.get)])


if __name__ == "__main__":
    print("UML Model Comparator with Recall, Precision, Overlap, and CSV Output\n")

    models = {}
    file_paths = {
        "Claude": "claude.json",
        "Gemini": "gemini.json",
        "Groq": "groq.json"
    }

    for model_name, path in file_paths.items():
        if not os.path.exists(path):
            print(f"❌ File not found: {path}")
            exit()
        models[model_name] = load_model_from_json(path)

    comparison_result, all_classes, all_relationships = compare_models(models)

    print("\n=== Class Comparison ===")
    for cls, model_list in comparison_result["classes"].items():
        print(f"Class: {cls} -> Present in: {model_list}")

    print("\n=== Relationship Comparison ===")
    for rel, model_list in comparison_result["relationships"].items():
        print(f"Relationship: {rel} -> Present in: {model_list}")

    scores, metrics = evaluate_models(models, all_classes, all_relationships, comparison_result)

    print("\n=== Model Scores ===")
    for model, score in scores.items():
        print(f"{model}: {score:.3f} points")

    best_model = max(scores, key=scores.get)
    print(f"\nThe BEST model is: {best_model}")

    save_results_to_csv(comparison_result, scores, metrics)
    print("\n✅ Results saved to 'uml_comparison_results.csv'")
