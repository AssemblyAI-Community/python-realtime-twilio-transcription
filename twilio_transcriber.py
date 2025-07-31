import os
import threading
from typing import Type
import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    TerminationEvent,
    TurnEvent,
)
from dotenv import load_dotenv
load_dotenv()

aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')

TWILIO_SAMPLE_RATE = 8000 # Hz
BUFFER_SIZE_MS = 100  # Buffer audio for 100ms before sending
BYTES_PER_MS = TWILIO_SAMPLE_RATE // 1000  # 8 bytes per ms at 8kHz


def on_begin(client: StreamingClient, event: BeginEvent):
    print(f"Transcription session started")

def on_turn(client: StreamingClient, event: TurnEvent):
    if event.transcript.strip():  # Only print non-empty transcripts
        # Check if this is a formatted turn
        is_formatted = hasattr(event, 'turn_is_formatted') and event.turn_is_formatted
        
        if is_formatted:
            print(f"FINAL (formatted): {event.transcript}")
        elif event.end_of_turn:
            print(f"FINAL (unformatted): {event.transcript}")
        else:
            print(f"PARTIAL: {event.transcript}")

def on_terminated(client: StreamingClient, event: TerminationEvent):
    print(f"Session ended - {event.audio_duration_seconds} seconds processed")

def on_error(client: StreamingClient, error: StreamingError):
    print(f"Error: {error}")


class TwilioTranscriber(StreamingClient):
    def __init__(self):
        # Create options for the StreamingClient
        options = StreamingClientOptions(
            api_key=aai.settings.api_key,
            api_host="streaming.assemblyai.com"  # Correct host for Universal-Streaming v3
        )
        
        # Initialize the parent StreamingClient with options
        super().__init__(options)
        
        # Register event handlers using the .on() method
        self.on(StreamingEvents.Begin, on_begin)
        self.on(StreamingEvents.Turn, on_turn)  
        self.on(StreamingEvents.Termination, on_terminated)
        self.on(StreamingEvents.Error, on_error)
        
        # Audio buffering
        self.audio_buffer = bytearray()
        self.buffer_size_bytes = BUFFER_SIZE_MS * BYTES_PER_MS  # 100ms of audio (800 bytes)
        self.buffer_lock = threading.Lock()
        self.is_active = False
    
    def start_transcription(self):
        """Start the transcription session"""
        params = StreamingParameters(
            sample_rate=TWILIO_SAMPLE_RATE,
            encoding=aai.AudioEncoding.pcm_mulaw,
            format_turns=True  # Enable formatted transcripts
        )
        self.is_active = True
        self.connect(params)
    
    def stream_audio(self, audio_data: bytes):
        """Buffer and stream audio data to AssemblyAI"""
        if not self.is_active:
            return
            
        with self.buffer_lock:
            self.audio_buffer.extend(audio_data)
            
            # If buffer is large enough, flush it
            if len(self.audio_buffer) >= self.buffer_size_bytes:
                self._flush_buffer()
    
    def _flush_buffer(self):
        """Send buffered audio to AssemblyAI"""
        if len(self.audio_buffer) > 0:
            # Send the buffered audio
            buffered_audio = bytes(self.audio_buffer)
            try:
                self.stream(buffered_audio)
            except Exception as e:
                print(f"Error sending audio: {e}")
            
            # Clear the buffer
            self.audio_buffer.clear()
    
    def stop_transcription(self):
        """Stop the transcription and clean up"""
        self.is_active = False
        
        # Flush any remaining audio
        with self.buffer_lock:
            if len(self.audio_buffer) > 0:
                self._flush_buffer()
        
        self.disconnect(terminate=True)
