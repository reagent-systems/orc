import json
import uuid
from datetime import datetime

task = {
    'id': str(uuid.uuid4()),
    'description': 'Create a simple Python script that prints "Hello from Python!"',
    'type': 'simple_task',
    'requirements': ['file_operations'],
    'priority': 'medium',
    'context': {
        'original_goal': 'Create a Python script',
        'test_task': True
    },
    'created_at': datetime.utcnow().isoformat(),
    'max_retries': 3,
    'retry_count': 0
}

task_file = f'workspace/tasks/pending/{task["id"]}.json'
with open(task_file, 'w') as f:
    json.dump(task, f, indent=2)

print(f'✅ Created task: {task["id"]}')
print(f'📁 Task file: {task_file}')
print(f'📝 Description: {task["description"]}') 