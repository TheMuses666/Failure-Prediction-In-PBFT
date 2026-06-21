from pathlib import Path

# =========================
# Project paths
# =========================

ROOT_DIR = Path(__file__).resolve().parent

DATA_RAW_DIR = ROOT_DIR / 'data' / 'raw'
DATA_PROCESSED_DIR = ROOT_DIR / 'data' / 'processed'
RESULTS_FIGURES_DIR = ROOT_DIR / 'results' / 'figures'
RESULTS_METRICS_DIR = ROOT_DIR / 'results' / 'metrics'
RESULTS_MODELS_DIR = ROOT_DIR / 'results' / 'models'

# =========================
# Simulation Setting
# =========================

NUM_NODES = 7
NUM_BYZANTINE_NODES = 2
NUM_NORMAL_NODES = NUM_NODES - NUM_BYZANTINE_NODES
PBFT_MIN_NODES_REQUIREMENT = 3*NUM_BYZANTINE_NODES + 1

FAULT_TYPES = ['silent', 'replay','equivocation','delay']   
ROUNDS_PER_FAULT = 200
NORMAL_ROUNDS = 400

TOTAL_SIMULATION_ROUNDS = ROUNDS_PER_FAULT * len(FAULT_TYPES) + NORMAL_ROUNDS

RANDOM_SEED = 42

STRICT_ROUND_VALIDATION = True

# =========================
# Label definition
# =========================

LABEL_NORMAL = 0
LABEL_DEGRADED = 1
LABEL_FAILURE = 2

LABEL_NAMES = {
    LABEL_NORMAL: "normal",
    LABEL_DEGRADED: "degraded",
    LABEL_FAILURE: "failure"
}

NORMAL_LATENCY_THRESHOLD_MAX = 50
DEGRADED_LATENCY_THRESHOLD_MAX = 150

# =========================
# Train Split
# =========================

TRAIN_RATIO = 0.7
VAL_RATIO = 0.1
TEST_RATIO = 0.2

MODEL_NAMES = [
    "decision_tree",
    "random_forest",
    "xgboost"
]

# =========================
# Feature set
# =========================

FEATURE_COLUMNS = [
    # Network layer
    "message_latency",
    "message_drop_rate",
    "propagation_pattern",

    # Consensus layer
    "consensus_agreement_time",
    "phase_completion_time",
    "timeout_frequency",
    "leader_change_frequency",
    "response_time",

    # Behaviour layer
    "voting_consistency",
    "message_consistency",
    "vote_deviation"
]

AUXILIARY_COLUMNS = [
    # Per-round event counters
    "forged",
    "replayed",
    "same_round_replayed",
    "stale_replayed",
    "equivocated",
    "delayed",

    # FaultInjector configuration snapshot
    "silent_mode",
    "delay_probability",
    "delay_distribution",
    "strict_round_validation",
]

TARGET_COLUMN = "label"

# =========================
# Network settings
# =========================

BASE_MESSAGE_LATENCY_MS = 20
LATENCY_JITTER_MS = 10
MESSAGE_DROP_PROBABILITY = 0.02

CONSENSUS_TIMEOUT_MS = 150
BYZANTINE_DELAY_MS = 300

# =========================
# Output files
# =========================

RAW_DATA_FILE = DATA_RAW_DIR / "consensus_data.csv"
PROCESSED_DATA_FILE = DATA_PROCESSED_DIR/ "processed_consensus_data.csv"

METRICS_FILE = RESULTS_METRICS_DIR / "model_metrics.csv"

# =========================
# Experiments
# =========================

SCALABILITY_NODE_COUNTS = [7, 10, 13]
ROBUSTNESS_BYZANTINE_RATIOS = [0.1, 0.2, 0.3]


# Phase 7 写 CSV 之前调用一次，确保 extract_features 的 keys
# 跟 FEATURE_COLUMNS + AUXILIARY_COLUMNS 完全对得上。
def assert_feature_schema(feature_dict: dict) -> None:
    expected = set(FEATURE_COLUMNS) | set(AUXILIARY_COLUMNS)
    actual = set(feature_dict.keys())
    missing = expected - actual
    extra = actual - expected
    assert not missing, f"Missing from feature_dict: {missing}"
    assert not extra, f"Unknown keys in feature_dict: {extra}"