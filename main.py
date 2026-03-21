from run_agent_once import run_once

if __name__ == '__main__':
    print("Running agent once...")
    summary = run_once(max_emails=10)
    print(summary['message'])