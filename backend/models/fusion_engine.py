class FusionEngine:
    def __init__(self):
        self.emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        self.modality_weights = {'visual': 1.15, 'text': 1.0, 'audio': 0.9}
        self.previous_scores = None
        self.smoothing = 0.35

    def fuse(self, visual_data, text_data, audio_data, active_modalities):
        """
        Fuses modalities based on what is active.
        active_modalities is a list of strings e.g. ['visual', 'text']
        """
        fused_scores = {e: 0.0 for e in self.emotions}
        total_weight = 0.0
        
        if 'visual' in active_modalities and visual_data:
            # support either raw emotion dict or structured dict containing 'emotions'
            vis_ems = visual_data.get('emotions', visual_data) if isinstance(visual_data, dict) else {}
            weight = self.modality_weights['visual']
            for e in self.emotions:
                fused_scores[e] += vis_ems.get(e, 0.0) * weight
            total_weight += weight
            
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
                
            weight = self.modality_weights['text']
            for e in self.emotions:
                fused_scores[e] += tex_ems.get(e, 0.0) * weight
            total_weight += weight
            
        if 'audio' in active_modalities and audio_data:
            # support structured dict containing 'emotions'
            aud_ems = audio_data.get('emotions', audio_data) if isinstance(audio_data, dict) else {}
            weight = self.modality_weights['audio']
            for e in self.emotions:
                fused_scores[e] += aud_ems.get(e, 0.0) * weight
            total_weight += weight
            
        if total_weight == 0:
            self.previous_scores = None
            return {e: 0.0 for e in self.emotions}
            
        # Weighted late fusion with short-term session memory to reduce jitter.
        for e in self.emotions:
            fused_scores[e] /= total_weight
            
        # Normalize
        total = sum(fused_scores.values()) + 1e-6
        normalized = {k: v/total for k, v in fused_scores.items()}

        if self.previous_scores:
            normalized = {
                e: normalized[e] * (1.0 - self.smoothing) + self.previous_scores[e] * self.smoothing
                for e in self.emotions
            }
            smoothed_total = sum(normalized.values()) + 1e-6
            normalized = {k: v / smoothed_total for k, v in normalized.items()}

        self.previous_scores = normalized
        return normalized
