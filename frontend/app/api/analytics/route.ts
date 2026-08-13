import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const execAsync = promisify(exec);
const BACKEND_DIR = path.resolve(process.cwd(), '../backend');

export const revalidate = 0;

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const channel = searchParams.get('channel') || 'all';

    const script = `
import sys, json
sys.path.insert(0, 'src')
import db
print(json.dumps(db.get_analytics_summary(channel_filter=${JSON.stringify(channel)})))
`.trim();

    const b64 = Buffer.from(script).toString('base64');
    const cmd = `uv run python -c "import base64; exec(base64.b64decode('${b64}').decode('utf-8'))"`;

    const { stdout } = await execAsync(cmd, { cwd: BACKEND_DIR });
    const summary = JSON.parse(stdout.trim());
    return NextResponse.json({ success: true, summary });
  } catch (error) {
    const errMessage = error instanceof Error ? error.message : 'Failed to fetch analytics summary';
    return NextResponse.json({ success: false, error: errMessage, summary: null }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const status = body.status || 'successful'; // 'successful' or 'failed'
    const failureCategory =
      body.failure_category || (status === 'failed' ? 'incomplete_task' : 'none');
    const outcomeSummary =
      body.outcome_summary ||
      (status === 'successful'
        ? 'Simulated triage completed: GREEN'
        : 'Simulated caller hangup before triage');
    const channel = body.channel || 'browser';
    const durationSeconds = body.duration_seconds || (status === 'successful' ? 42 : 4);
    const latencyMs = body.latency_ms || 420.0;

    const script = `
import sys, json
sys.path.insert(0, 'src')
import db
res = db.log_simulated_call(
    status=${JSON.stringify(status)},
    failure_category=${JSON.stringify(failureCategory)},
    outcome_summary=${JSON.stringify(outcomeSummary)},
    channel=${JSON.stringify(channel)},
    duration_seconds=${Number(durationSeconds)},
    latency_ms=${Number(latencyMs)}
)
print(json.dumps(res))
`.trim();

    const b64 = Buffer.from(script).toString('base64');
    const cmd = `uv run python -c "import base64; exec(base64.b64decode('${b64}').decode('utf-8'))"`;

    const { stdout } = await execAsync(cmd, { cwd: BACKEND_DIR });
    const result = JSON.parse(stdout.trim());
    return NextResponse.json({ success: true, result });
  } catch (error) {
    const errMessage = error instanceof Error ? error.message : 'Failed to create simulated call';
    return NextResponse.json({ success: false, error: errMessage }, { status: 500 });
  }
}
