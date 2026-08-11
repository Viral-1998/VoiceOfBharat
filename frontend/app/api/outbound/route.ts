import { NextResponse } from 'next/server';
import {
  AccessToken,
  type AccessTokenOptions,
  SipClient,
  type VideoGrant,
} from 'livekit-server-sdk';
import { RoomConfiguration } from '@livekit/protocol';

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const AGENT_NAME = process.env.AGENT_NAME ?? 'my-agent';
const SIP_TRUNK_ID = process.env.SIP_TRUNK_ID;

export const revalidate = 0;

export async function POST(req: Request) {
  try {
    if (LIVEKIT_URL === undefined || API_KEY === undefined || API_SECRET === undefined) {
      return NextResponse.json(
        {
          error:
            'LiveKit environment variables (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) are missing.',
        },
        { status: 500 }
      );
    }

    const body = await req.json().catch(() => ({}));
    const phoneNumber = body.phone_number || '+919876543210';
    const patientName = body.patient_name || 'Ramesh Kumar';
    const reminderType = body.reminder_type || 'Medication & Vaccination Follow-up';
    const sipTrunkId = body.sip_trunk_id || SIP_TRUNK_ID;

    const callId = `outbound_${Math.floor(Math.random() * 100000)}`;
    const roomName = `outbound_room_${callId}`;

    const metadataObj = {
      is_outbound: true,
      call_id: callId,
      phone_number: phoneNumber,
      patient_name: patientName,
      reminder_type: reminderType,
    };

    const roomConfig = RoomConfiguration.fromJson(
      { agents: [{ agentName: AGENT_NAME }] },
      { ignoreUnknownFields: true }
    );

    let cleanSipCallTo = phoneNumber.trim();
    if (cleanSipCallTo.startsWith('sip:')) {
      cleanSipCallTo = cleanSipCallTo.slice(4);
    }
    if (cleanSipCallTo.includes('@')) {
      cleanSipCallTo = cleanSipCallTo.split('@')[0];
    }

    const participantName = `Patient: ${patientName}`;
    const participantIdentity = `phone_${cleanSipCallTo.replace(/[^a-zA-Z0-9_-]/g, '_')}_${callId}`;

    let sipDispatched = false;
    if (sipTrunkId) {
      try {
        const sipClient = new SipClient(LIVEKIT_URL, API_KEY, API_SECRET);
        await sipClient.createSipParticipant(sipTrunkId, cleanSipCallTo, roomName, {
          participantIdentity: `phone_${cleanSipCallTo.replace(/[^a-zA-Z0-9_-]/g, '_')}`,
          participantName: patientName,
        });
        sipDispatched = true;
      } catch (err) {
        console.warn('SipClient createSipParticipant warning:', err);
      }
    }

    const participantToken = await createParticipantToken(
      { identity: participantIdentity, name: participantName },
      roomName,
      roomConfig,
      JSON.stringify(metadataObj)
    );

    return NextResponse.json({
      success: true,
      call_id: callId,
      room_name: roomName,
      phone_number: phoneNumber,
      patient_name: patientName,
      reminder_type: reminderType,
      sip_trunk_id: sipTrunkId ?? null,
      sip_dispatched: sipDispatched,
      server_url: LIVEKIT_URL,
      participant_token: participantToken,
      participant_name: participantName,
    });
  } catch (error) {
    const errMessage =
      error instanceof Error ? error.message : 'Unknown error during outbound dispatch';
    return NextResponse.json({ error: errMessage }, { status: 500 });
  }
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  roomConfig?: RoomConfiguration,
  metadata?: string
): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: '15m',
    metadata: metadata,
  });
  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  if (roomConfig) {
    at.roomConfig = roomConfig;
  }

  return at.toJwt();
}
