import { useEffect } from 'react';
import { Room, RoomEvent } from 'livekit-client';
import {
  RoomAudioRenderer,
  type RoomAudioRendererProps,
  SessionProvider,
  type SessionProviderProps,
  type UseSessionReturn,
} from '@livekit/components-react';

/**
 * Props for the AgentSessionProvider component.
 * Combines SessionProviderProps with RoomAudioRendererProps.
 */
export type AgentSessionProviderProps = SessionProviderProps &
  RoomAudioRendererProps & {
    /**
     * The room to provide.
     */
    room?: Room;
    /**
     * The volume to set for the audio renderer.
     */
    volume?: number;
    /**
     * Whether to mute the audio renderer.
     */
    muted?: boolean;
    /**
     * The session to provide.
     */
    session: UseSessionReturn;
    /**
     * The children to render.
     */
    children: React.ReactNode;
  };

/**
 * A provider component for agent sessions that wraps SessionProvider
 * and includes RoomAudioRenderer for audio playback.
 *
 * @example
 * ```tsx
 * <AgentSessionProvider session={agentSession}>
 *   <AgentControlBar />
 *   <AgentChatTranscript />
 * </AgentSessionProvider>
 * ```
 */
export function AgentSessionProvider({
  session,
  children,
  room,
  ...roomAudioRendererProps
}: AgentSessionProviderProps) {
  const activeRoom = room ?? session.room;

  useEffect(() => {
    if (!activeRoom) return;

    // Handle agent events data stream topic (lk.agent.events) to prevent "no handler" warning
    const handleDataReceived = () => {
      // Event stream handled cleanly
    };

    activeRoom.on(RoomEvent.DataReceived, handleDataReceived);

    return () => {
      activeRoom.off(RoomEvent.DataReceived, handleDataReceived);
    };
  }, [activeRoom]);

  return (
    <SessionProvider session={session}>
      {children}
      <RoomAudioRenderer room={activeRoom} {...roomAudioRendererProps} />
    </SessionProvider>
  );
}
