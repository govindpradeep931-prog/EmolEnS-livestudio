class FusionEngine:
    def __init__(self):
        self.emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

    def fuse(self, visual_data, text_data, audio_data, active_modalities):
        """
        Fuses modalities based on what is active.
        active_modalities is a list of strings e.g. ['visual', 'text']
        """
        fused_scores = {e: 0.0 for e in self.emotions}
        count = 0
        
        if 'visual' in active_modalities and visual_data:
            # support either raw emotion dict or structured dict containing 'emotions'
            vis_ems = visual_data.get('emotions', visual_data) if isinstance(visual_data, dict) else {}
            for e in self.emotions:
                fused_scores[e] += vis_ems.get(e, 0.0)
            count += 1
            
        if 'text' in active_modalities and text_data:
            # text_data can contain 'transformer' or 'lexicon' or raw keys
            tex_ems = {}
            if isinstance(text_data, dict):
                # Late-fuse lexicon and transformer internally
                lex = text_data.get('lexicon', {})
                trans = text_data.get('transformer', {})
                for e in self.emotions:
                    scores = []
                    if e in lex: scores.append(lex[e])
                    if e in trans: scores.append(trans[e])
                    tex_ems[e] = sum(scores) / len(scores) if scores else 0.0
            else:
                tex_ems = text_data
                
            for e in self.emotions:
                fused_scores[e] += tex_ems.get(e, 0.0)
            count += 1
            
        if 'audio' in active_modalities and audio_data:
            # support structured dict containing 'emotions'
            aud_ems = audio_data.get('emotions', audio_data) if isinstance(audio_data, dict) else {}
            for e in self.emotions:
                fused_scores[e] += aud_ems.get(e, 0.0)
            count += 1
            
        if count == 0:
            return {e: 0.0 for e in self.emotions}
            
        # Average fusion (Late Fusion)
        for e in self.emotions:
            fused_scores[e] /= count
            
        # Normalize
        total = sum(fused_scores.values()) + 1e-6
        return {k: v/total for k, v in fused_scores.items()}
