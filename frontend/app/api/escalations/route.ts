import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const execAsync = promisify(exec);
const BACKEND_DIR = path.resolve(process.cwd(), '../backend');

export const revalidate = 0;

export async function GET() {
  try {
    const script = `
import sys, json
sys.path.insert(0, 'src')
import db
print(json.dumps(db.get_escalation_requests()))
`.trim();

    const b64 = Buffer.from(script).toString('base64');
    const cmd = `uv run python -c "import base64; exec(base64.b64decode('${b64}').decode('utf-8'))"`;

    const { stdout } = await execAsync(cmd, { cwd: BACKEND_DIR });
    const requests = JSON.parse(stdout.trim());
    return NextResponse.json({ success: true, requests });
  } catch (error) {
    const errMessage =
      error instanceof Error ? error.message : 'Failed to fetch escalation requests';
    return NextResponse.json({ success: false, error: errMessage, requests: [] }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const userId = body.user_id || 'manual_user';
    const reason = body.reason || 'Red-flag Emergency Symptom';
    const summary = body.summary || 'Emergency caller reported chest pain and shortness of breath.';
    const callerName = body.caller_name || 'Ramesh Kumar';
    const phoneNumber = body.phone_number || '+919876543210';
    const urgency = body.urgency || 'emergency';
    const callerLanguage = body.caller_language || 'English';
    const preferredFollowup = body.preferred_followup || 'phone_call';

    const script = `
import sys, json
sys.path.insert(0, 'src')
import db
res = db.create_escalation_request(
    user_id=${JSON.stringify(userId)},
    reason=${JSON.stringify(reason)},
    summary=${JSON.stringify(summary)},
    caller_name=${JSON.stringify(callerName)},
    phone_number=${JSON.stringify(phoneNumber)},
    urgency=${JSON.stringify(urgency)},
    caller_language=${JSON.stringify(callerLanguage)},
    preferred_followup=${JSON.stringify(preferredFollowup)},
    permission_granted=True
)
print(json.dumps(res))
`.trim();

    const b64 = Buffer.from(script).toString('base64');
    const cmd = `uv run python -c "import base64; exec(base64.b64decode('${b64}').decode('utf-8'))"`;

    const { stdout } = await execAsync(cmd, { cwd: BACKEND_DIR });
    const result = JSON.parse(stdout.trim());
    return NextResponse.json({ success: true, request: result });
  } catch (error) {
    const errMessage =
      error instanceof Error ? error.message : 'Failed to create escalation request';
    return NextResponse.json({ success: false, error: errMessage }, { status: 500 });
  }
}

export async function PATCH(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const requestId = body.id;
    const status = body.status;

    if (!requestId || !status) {
      return NextResponse.json({ error: 'Missing id or status' }, { status: 400 });
    }

    const script = `
import sys, json
sys.path.insert(0, 'src')
import db
ok = db.update_escalation_status(${JSON.stringify(requestId)}, ${JSON.stringify(status)})
print(json.dumps({'success': ok}))
`.trim();

    const b64 = Buffer.from(script).toString('base64');
    const cmd = `uv run python -c "import base64; exec(base64.b64decode('${b64}').decode('utf-8'))"`;

    const { stdout } = await execAsync(cmd, { cwd: BACKEND_DIR });
    const result = JSON.parse(stdout.trim());
    return NextResponse.json({ success: result.success });
  } catch (error) {
    const errMessage =
      error instanceof Error ? error.message : 'Failed to update escalation status';
    return NextResponse.json({ success: false, error: errMessage }, { status: 500 });
  }
}
