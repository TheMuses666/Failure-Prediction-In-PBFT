import matplotlib.pyplot as plt
from src.simulation.pbft import run_pbft_simulation
from config import RESULTS_FIGURES_DIR, BYZ_IDS, CONSENSUS_TIMEOUT_MS

COLORS = {
    'pre_prepare': 'tab:blue',
    'prepare': 'tab:orange',
    'commit': 'tab:green',
}


def draw_round(ax, raw, title):
    net = raw['_network']
    for m in net.message_log:
        if m.delivery_time is None:
            continue
        color = COLORS.get(m.message_type, 'gray')
        style = '--' if m.fault_type else '-'
        ax.plot([m.send_time, m.delivery_time],
                [m.receiver_id, m.receiver_id],
                color=color, linestyle=style, alpha=0.5, linewidth=1.2)
        ax.plot(m.delivery_time, m.receiver_id, marker='|',
                color=color, markersize=8)

    ax.axvline(CONSENSUS_TIMEOUT_MS, color='red', linestyle=':', alpha=0.7)
    ax.text(CONSENSUS_TIMEOUT_MS + 2, 0.2, 'timeout', color='red', fontsize=8)
    ax.set_title(title)
    ax.set_xlabel('Simulated time (ms)')
    ax.set_yticks(range(len(net.nodes)))
    ax.grid(True, alpha=0.3, axis='x')


def main():
    normal = run_pbft_simulation(n_rounds=1, fault_type='normal',
                                 byzantine_node_ids=[], start_round=1)[0]
    delay = run_pbft_simulation(n_rounds=1, fault_type='delay',
                                byzantine_node_ids=BYZ_IDS, start_round=1)[0]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True, sharex=True)
    draw_round(ax1, normal, 'Normal round')
    draw_round(ax2, delay, f'Delay-fault round (Byzantine nodes {BYZ_IDS})')
    ax1.set_ylabel('Receiver node id')

    handles = [plt.Line2D([0], [0], color=c, label=t) for t, c in COLORS.items()]
    handles.append(plt.Line2D([0], [0], color='gray', linestyle='--',
                              label='fault-affected message'))
    ax2.legend(handles=handles, loc='center left', bbox_to_anchor=(1.02, 0.5))

    fig.suptitle('PBFT round message timeline (each line = one message, send to delivery)')
    fig.tight_layout()
    out_path = RESULTS_FIGURES_DIR / 'pbft_round_timeline.png'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Figure saved --> {out_path}')


if __name__ == '__main__':
    main()
