using System;
using System.Collections.Generic;
using System.Speech.Synthesis;
public class TreeSpeechMark {
    public double start {get;set;}
    public int position {get;set;}
    public int length {get;set;}
    public string text {get;set;}
}
public class TreeSpeechCapture {
    public static TreeSpeechMark[] Speak(SpeechSynthesizer synth, string text, string filename) {
        var marks = new List<TreeSpeechMark>();
        EventHandler<SpeakProgressEventArgs> handler = (sender,e) => {
            marks.Add(new TreeSpeechMark {start=e.AudioPosition.TotalSeconds,position=e.CharacterPosition,length=e.CharacterCount,text=e.Text});
        };
        synth.SpeakProgress += handler;
        synth.SetOutputToWaveFile(filename, new System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, System.Speech.AudioFormat.AudioBitsPerSample.Sixteen, System.Speech.AudioFormat.AudioChannel.Mono));
        synth.Speak(text);
        synth.SetOutputToNull();
        synth.SpeakProgress -= handler;
        return marks.ToArray();
    }
}
