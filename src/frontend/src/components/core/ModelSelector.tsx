import { useState, useEffect } from "react";
import {
  Dropdown,
  Option,
  Label,
  makeStyles,
  Spinner,
} from "@fluentui/react-components";
import config from "~/config";

const useStyles = makeStyles({
  container: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    minWidth: "200px",
  },
  label: {
    fontWeight: "600",
  },
  dropdown: {
    minWidth: "200px",
  },
});

interface Model {
  id: string;
  name: string;
  provider: string;
}

interface ModelSelectorProps {
  selectedModel: string | null;
  onModelChange: (modelId: string) => void;
}

export function ModelSelector({ selectedModel, onModelChange }: ModelSelectorProps) {
  const styles = useStyles();
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${config.apiBaseUrl}/models`, {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.models && Array.isArray(data.models)) {
        setModels(data.models);

        // Set first model as default if none selected
        if (!selectedModel && data.models.length > 0) {
          onModelChange(data.models[0].id);
        }
      } else {
        throw new Error("Invalid response format");
      }
    } catch (err) {
      console.error("Error fetching models:", err);
      setError(err instanceof Error ? err.message : "Failed to load models");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <Label className={styles.label}>Model</Label>
        <Spinner size="tiny" label="Loading models..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <Label className={styles.label}>Model</Label>
        <div style={{ color: "red", fontSize: "12px" }}>{error}</div>
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <div className={styles.container}>
        <Label className={styles.label}>Model</Label>
        <div style={{ fontSize: "12px" }}>No models available</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <Label className={styles.label}>Model</Label>
      <Dropdown
        className={styles.dropdown}
        value={selectedModel || models[0]?.id || ""}
        selectedOptions={[selectedModel || models[0]?.id || ""]}
        onOptionSelect={(_, data) => {
          if (data.optionValue) {
            onModelChange(data.optionValue);
          }
        }}
        placeholder="Select a model"
      >
        {models.map((model) => (
          <Option key={model.id} value={model.id}>
            {model.name}
            {model.provider && model.provider !== "azure" && (
              <span style={{ color: "#888", fontSize: "11px", marginLeft: "8px" }}>
                ({model.provider})
              </span>
            )}
          </Option>
        ))}
      </Dropdown>
    </div>
  );
}
