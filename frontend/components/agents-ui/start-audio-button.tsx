import { type ComponentProps } from 'react';
import { Room } from 'livekit-client';
import { useEnsureRoom, useStartAudio } from '@livekit/components-react';
import { Button } from '@/components/ui/button';

/**
 * Props for the StartAudioButton component.
 */
export interface StartAudioButtonProps extends ComponentProps<'button'> {
  /**
   * The size of the button.
   * @defaultValue 'default'
   */
  size?: 'default' | 'sm' | 'lg' | 'icon' | 'icon-sm' | 'icon-lg';
  /**
   * The variant of the button.
   * @defaultValue 'default'
   */
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  /**
   * The LiveKit room instance. If not provided, uses the room from context.
   */
  room?: Room;
  /**
   * The label text to display on the button.
   */
  label: string;
}

/**
 * A button that allows users to start audio playback.
 * Required for browsers that block autoplay of audio.
 * Only renders when audio playback is blocked.
 *
 * @extends ComponentProps<'button'>
 *
 * @example
 * ```tsx
 * <StartAudioButton label="Click to allow audio playback" />
 * ```
 */
export function StartAudioButton({
  size = 'default',
  variant = 'default',
  label,
  room,
  ...props
}: StartAudioButtonProps) {
  const roomEnsured = useEnsureRoom(room);
  const { mergedProps } = useStartAudio({ room: roomEnsured, props });

  // If mergedProps style display is none, livekit hides the button (audio is allowed)
  if (mergedProps.style?.display === 'none') {
    return null;
  }

  return (
    <div className="fixed top-6 left-1/2 z-[100] -translate-x-1/2 animate-bounce">
      <Button
        size="lg"
        variant={variant}
        {...props}
        {...mergedProps}
        className="flex cursor-pointer items-center gap-2 rounded-full border border-white/50 bg-cyan-500 px-6 py-3 font-mono text-xs font-bold text-slate-950 uppercase shadow-[0_0_30px_rgba(6,182,212,0.8)] hover:bg-cyan-400"
      >
        <span>🔊</span>
        <span>{label || 'CLICK TO ENABLE VOICE AUDIO'}</span>
      </Button>
    </div>
  );
}
