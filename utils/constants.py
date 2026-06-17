"""
Project-wide constants.
"""

# =========================
# Node states
# =========================

HONEST_NODE = "honest"
BYZANTINE_NODE = "byzantine"

# =========================
# PBFT phases
# =========================

PRE_PREPARE = "PRE_PREPARE"
PREPARE = "PREPARE"
COMMIT = "COMMIT"
REPLY = "REPLY"

PBFT_PHASES = [
    PRE_PREPARE,
    PREPARE,
    COMMIT,
    REPLY
]

# =========================
# Fault types
# =========================

FAULT_NONE = "normal"

FAULT_SILENT = "silent"
FAULT_REPLAY = "replay"
FAULT_EQUIVOCATION = "equivocation"
FAULT_DELAY = "delay"

FAULT_TYPES = [
    FAULT_SILENT,
    FAULT_REPLAY,
    FAULT_EQUIVOCATION,
    FAULT_DELAY
]

# =========================
# Label classes
# =========================

LABEL_NORMAL = 0
LABEL_DEGRADED = 1
LABEL_FAILURE = 2

LABEL_MAPPING = {
    LABEL_NORMAL: "Normal",
    LABEL_DEGRADED: "Degraded",
    LABEL_FAILURE: "Failure"
}

# =========================
# Message status
# =========================

MESSAGE_SENT = "sent"
MESSAGE_RECEIVED = "received"
MESSAGE_DROPPED = "dropped"
MESSAGE_DELAYED = "delayed"

# =========================
# Consensus result
# =========================

CONSENSUS_SUCCESS = "success"
CONSENSUS_DEGRADED = "degraded"
CONSENSUS_FAILED = "failed"

# =========================
# Dataset columns
# =========================

MESSAGE_LATENCY = "message_latency"
MESSAGE_DROP_RATE = "message_drop_rate"
PROPAGATION_PATTERN = "propagation_pattern"

CONSENSUS_AGREEMENT_TIME = "consensus_agreement_time"
PHASE_COMPLETION_TIME = "phase_completion_time"
TIMEOUT_FREQUENCY = "timeout_frequency"
LEADER_CHANGE_FREQUENCY = "leader_change_frequency"
RESPONSE_TIME = "response_time"

VOTING_CONSISTENCY = "voting_consistency"
MESSAGE_CONSISTENCY = "message_consistency"
VOTE_DEVIATION = "vote_deviation"

TARGET_LABEL = "label"

FEATURE_COLUMNS = [
    MESSAGE_LATENCY,
    MESSAGE_DROP_RATE,
    PROPAGATION_PATTERN,
    CONSENSUS_AGREEMENT_TIME,
    PHASE_COMPLETION_TIME,
    TIMEOUT_FREQUENCY,
    LEADER_CHANGE_FREQUENCY,
    RESPONSE_TIME,
    VOTING_CONSISTENCY,
    MESSAGE_CONSISTENCY,
    VOTE_DEVIATION
]