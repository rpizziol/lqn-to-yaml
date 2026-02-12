import re
from dataclasses import dataclass, field
from typing import List, Dict

# --- Data Structures to hold the LQN model ---

@dataclass
class Call:
    target_entry: str
    call_type: str # 'y' for sync, 'z' for async
    num_calls: float = 1.0
    probability: float = 1.0

@dataclass
class Activity:
    name: str
    service_time: float
    calls: List[Call] = field(default_factory=list)

@dataclass
class Task:
    name: str
    processor_name: str
    multiplicity: int
    activities: Dict[str, Activity] = field(default_factory=dict)
    entry_name: str = ""

@dataclass
class LQNModel:
    tasks: Dict[str, Task] = field(default_factory=dict)
    # We can add processors, etc. later if needed

# --- Parser Logic ---

def parse_lqn_file(filepath: str) -> LQNModel:
    """
    Parses a .lqn text file and returns a structured LQNModel object.
    NOTE: This is a simplified parser focusing on Tasks, Activities, and Calls.
    """
    with open(filepath, 'r') as f:
        content = f.read()

    model = LQNModel()
    
    # --- Parse Tasks ---
    # Use regex to find the task declaration block
    task_block_match = re.search(r'# Tasks declaration\s*T 0\s*(.*?)\s*-1', content, re.DOTALL)
    if task_block_match:
        task_lines = task_block_match.group(1).strip().split('\n')
        for line in task_lines:
            parts = line.split() # e.g., ['t', 'Task0', 'r', 'Entr0', '-1', 'Proc0', 'm', '1']
            if parts[0] == 't':
                task_name = parts[1]
                model.tasks[task_name] = Task(
                    name=task_name,
                    entry_name=parts[3],
                    processor_name=parts[5],
                    multiplicity=int(parts[7])
                )

    # --- Parse Activities and Calls ---
    # Find all activity blocks (from 'A TaskName' to '-1')
    activity_blocks = re.findall(r'A (Task\d+)\s*(.*?)\s*-1', content, re.DOTALL)
    for task_name, block_content in activity_blocks:
        task = model.tasks.get(task_name)
        if not task:
            continue

        lines = block_content.strip().split('\n')
        current_activity = None
        
        # Simplified parsing logic
        for line in lines:
            line = line.strip()
            parts = line.split()
            if not parts:
                continue

            # Parse service time: 's acti0 1.23'
            if parts[0] == 's' and not current_activity:
                activity_name = parts[1]
                service_time = float(parts[2])
                current_activity = Activity(name=activity_name, service_time=service_time)
                task.activities[activity_name] = current_activity

            # Parse calls: 'y acti01 Entr1 1'
            if parts[0] in ['y', 'z']:
                call_type = parts[0]
                target_entry = parts[2]
                num_calls = float(parts[3])
                # Find its probability in the branching logic
                prob = 1.0 # Default
                # A more complex regex would be needed to extract probabilities from lines like:
                # 'acti1 -> (0.25)acti12 + ...'
                # For simplicity, we can add that logic later.
                
                if current_activity:
                    current_activity.calls.append(Call(
                        target_entry=target_entry,
                        call_type=call_type,
                        num_calls=num_calls,
                        probability=prob
                    ))

    return model
