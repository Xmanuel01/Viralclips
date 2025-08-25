"""
AI Script Generation Service
Generates engaging scripts from video transcriptions with platform-specific optimization
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import openai
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from keybert import KeyBERT
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

@dataclass
class ScriptSection:
    start_time: float
    end_time: float
    section_type: str  # 'hook', 'content', 'cta', 'transition'
    content: str
    engagement_score: float
    keywords: List[str]

@dataclass
class GeneratedScript:
    title: str
    content: str
    platform_optimization: str
    engagement_score: float
    sentiment_score: float
    keywords: List[str]
    hashtags: List[str]
    hooks: List[str]
    ctas: List[str]
    timestamps: List[ScriptSection]

class ScriptGenerator:
    def __init__(self):
        # Initialize AI models
        self.openai_client = openai.OpenAI()
        self.keybert = KeyBERT()
        
        # Initialize sentiment analysis
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True
            )
        except Exception:
            # Fallback to a simpler model
            self.sentiment_analyzer = pipeline("sentiment-analysis")
        
        # Initialize emotion detection
        try:
            self.emotion_analyzer = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                return_all_scores=True
            )
        except Exception:
            self.emotion_analyzer = None
        
        # Platform-specific prompts
        self.platform_prompts = {
            'tiktok': {
                'style': 'energetic, trendy, uses current slang, hook-heavy',
                'length': 'ultra-short sentences, punchy',
                'engagement': 'includes trending hashtags, calls for interaction',
                'structure': 'hook → quick value → strong CTA'
            },
            'youtube': {
                'style': 'informative yet engaging, storytelling approach',
                'length': 'medium-length sentences, detailed explanations',
                'engagement': 'encourages subscriptions and comments',
                'structure': 'hook → build curiosity → deliver value → subscribe CTA'
            },
            'instagram': {
                'style': 'visual-first, aesthetic language, lifestyle-focused',
                'length': 'medium sentences, descriptive',
                'engagement': 'encourages saves and shares',
                'structure': 'visual hook → story/value → save/share CTA'
            },
            'twitter': {
                'style': 'concise, tweet-worthy snippets, conversation-starter',
                'length': 'very short, thread-ready',
                'engagement': 'encourages retweets and replies',
                'structure': 'bold statement → context → discussion CTA'
            },
            'general': {
                'style': 'versatile, adaptable to multiple platforms',
                'length': 'balanced sentence length',
                'engagement': 'platform-agnostic engagement tactics',
                'structure': 'hook → value delivery → flexible CTA'
            }
        }
        
        # Viral keywords and phrases
        self.viral_keywords = {
            'hooks': [
                "You won't believe",
                "This changed everything",
                "Nobody talks about this",
                "The secret that",
                "What they don't tell you",
                "This will blow your mind",
                "The truth about",
                "Most people don't know",
                "Here's what happened when",
                "The mistake everyone makes"
            ],
            'transition_phrases': [
                "But here's the thing",
                "Here's where it gets interesting",
                "Now, this is crucial",
                "But wait, there's more",
                "This is where most people fail",
                "Here's the game-changer",
                "Now pay attention to this",
                "This next part is key"
            ],
            'cta_phrases': [
                "Let me know what you think",
                "Drop a comment below",
                "Share this with someone who needs to see it",
                "Save this for later",
                "Follow for more tips like this",
                "Which one surprised you most?",
                "Try this and tell me how it goes",
                "What's your experience with this?"
            ]
        }

    async def generate_script(
        self,
        transcription_text: str,
        video_duration: float,
        platform: str = 'general',
        custom_prompt: Optional[str] = None,
        include_timestamps: bool = True
    ) -> GeneratedScript:
        """Generate an engaging script from video transcription"""
        
        # Step 1: Analyze the transcription
        analysis = await self._analyze_transcription(transcription_text)
        
        # Step 2: Extract key moments and highlights
        highlights = await self._extract_highlights(transcription_text, video_duration)
        
        # Step 3: Generate platform-optimized script
        script_content = await self._generate_platform_script(
            transcription_text, analysis, highlights, platform, custom_prompt
        )
        
        # Step 4: Generate hashtags and CTAs
        hashtags = await self._generate_hashtags(analysis['keywords'], platform)
        ctas = await self._generate_ctas(platform)
        hooks = await self._generate_hooks(analysis['keywords'], platform)
        
        # Step 5: Create timestamps if requested
        timestamps = []
        if include_timestamps:
            timestamps = await self._create_timestamps(script_content, highlights)
        
        # Step 6: Calculate engagement score
        engagement_score = await self._calculate_engagement_score(
            script_content, analysis, platform
        )
        
        return GeneratedScript(
            title=await self._generate_title(analysis['keywords'], platform),
            content=script_content,
            platform_optimization=platform,
            engagement_score=engagement_score,
            sentiment_score=analysis['sentiment_score'],
            keywords=analysis['keywords'],
            hashtags=hashtags,
            hooks=hooks,
            ctas=ctas,
            timestamps=timestamps
        )

    async def _analyze_transcription(self, text: str) -> Dict[str, Any]:
        """Analyze transcription for sentiment, keywords, and key themes"""
        
        # Extract keywords using KeyBERT
        keywords = self.keybert.extract_keywords(
            text, 
            keyphrase_ngram_range=(1, 3), 
            stop_words='english',
            top_k=15
        )
        keyword_list = [kw[0] for kw in keywords]
        
        # Sentiment analysis
        sentiment_result = self.sentiment_analyzer(text[:512])  # Truncate for model limits
        if isinstance(sentiment_result[0], list):
            # Multiple scores returned
            sentiment_scores = {item['label'].lower(): item['score'] for item in sentiment_result[0]}
            overall_sentiment = max(sentiment_scores, key=sentiment_scores.get)
            sentiment_score = sentiment_scores.get('positive', 0) - sentiment_scores.get('negative', 0)
        else:
            # Single score returned
            overall_sentiment = sentiment_result[0]['label'].lower()
            sentiment_score = sentiment_result[0]['score'] if 'positive' in overall_sentiment else -sentiment_result[0]['score']
        
        # Emotion analysis if available
        emotions = {}
        if self.emotion_analyzer:
            try:
                emotion_result = self.emotion_analyzer(text[:512])
                emotions = {item['label']: item['score'] for item in emotion_result}
            except Exception:
                emotions = {}
        
        # TextBlob analysis for additional insights
        blob = TextBlob(text)
        
        return {
            'keywords': keyword_list,
            'sentiment_score': sentiment_score,
            'overall_sentiment': overall_sentiment,
            'emotions': emotions,
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity,
            'word_count': len(word_tokenize(text)),
            'sentence_count': len(sent_tokenize(text))
        }

    async def _extract_highlights(self, text: str, duration: float) -> List[Dict[str, Any]]:
        """Extract key moments and highlights from transcription"""
        
        sentences = sent_tokenize(text)
        highlights = []
        
        # Estimate time per sentence (rough calculation)
        time_per_sentence = duration / len(sentences) if sentences else 1
        
        # Analyze each sentence for viral potential
        for i, sentence in enumerate(sentences):
            start_time = i * time_per_sentence
            end_time = (i + 1) * time_per_sentence
            
            # Calculate importance score
            importance_score = await self._calculate_sentence_importance(sentence)
            
            if importance_score > 0.6:  # Threshold for highlights
                highlights.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'content': sentence,
                    'importance_score': importance_score,
                    'type': await self._classify_sentence_type(sentence)
                })
        
        # Sort by importance and return top highlights
        highlights.sort(key=lambda x: x['importance_score'], reverse=True)
        return highlights[:10]  # Return top 10 highlights

    async def _calculate_sentence_importance(self, sentence: str) -> float:
        """Calculate the viral potential of a sentence"""
        
        score = 0.0
        sentence_lower = sentence.lower()
        
        # Check for emotional words
        emotional_words = ['amazing', 'incredible', 'shocking', 'unbelievable', 'secret', 'truth', 'revealed']
        score += sum(0.1 for word in emotional_words if word in sentence_lower)
        
        # Check for numbers (specific data points are engaging)
        if re.search(r'\d+', sentence):
            score += 0.2
        
        # Check for question marks (engagement)
        if '?' in sentence:
            score += 0.15
        
        # Check for superlatives
        superlatives = ['best', 'worst', 'most', 'least', 'first', 'last', 'only', 'never', 'always']
        score += sum(0.1 for word in superlatives if word in sentence_lower)
        
        # Sentence length penalty (too long or too short)
        word_count = len(sentence.split())
        if 5 <= word_count <= 20:
            score += 0.1
        elif word_count > 30:
            score -= 0.2
        
        return min(score, 1.0)

    async def _classify_sentence_type(self, sentence: str) -> str:
        """Classify sentence as hook, content, cta, or transition"""
        
        sentence_lower = sentence.lower()
        
        # Hook indicators
        hook_indicators = ['you won\'t believe', 'this changed', 'secret', 'nobody talks', 'most people don\'t']
        if any(indicator in sentence_lower for indicator in hook_indicators):
            return 'hook'
        
        # CTA indicators
        cta_indicators = ['comment', 'like', 'subscribe', 'share', 'follow', 'let me know', 'tell me']
        if any(indicator in sentence_lower for indicator in cta_indicators):
            return 'cta'
        
        # Transition indicators
        transition_indicators = ['but', 'however', 'now', 'next', 'here\'s', 'so']
        if sentence_lower.startswith(tuple(transition_indicators)):
            return 'transition'
        
        return 'content'

    async def _generate_platform_script(
        self,
        transcription: str,
        analysis: Dict[str, Any],
        highlights: List[Dict[str, Any]],
        platform: str,
        custom_prompt: Optional[str] = None
    ) -> str:
        """Generate platform-optimized script using OpenAI"""
        
        platform_config = self.platform_prompts.get(platform, self.platform_prompts['general'])
        
        # Build the prompt
        system_prompt = f"""You are an expert social media content creator specializing in viral {platform} content.
        
Platform Style: {platform_config['style']}
Content Length: {platform_config['length']}
Engagement Strategy: {platform_config['engagement']}
Content Structure: {platform_config['structure']}

Your task is to transform the provided video transcription into an engaging, viral-ready script optimized for {platform}.

Key Requirements:
1. Create a compelling hook within the first 3 seconds
2. Maintain high engagement throughout
3. Include natural transitions between key points
4. End with a strong call-to-action
5. Use the platform's specific language and style
6. Incorporate trending elements when appropriate
"""
        
        user_prompt = f"""
Original Video Transcription:
{transcription[:2000]}  # Truncate to avoid token limits

Key Highlights Identified:
{json.dumps([h['content'] for h in highlights[:5]], indent=2)}

Top Keywords: {', '.join(analysis['keywords'][:10])}
Overall Sentiment: {analysis['overall_sentiment']}

{f"Additional Instructions: {custom_prompt}" if custom_prompt else ""}

Please create an engaging {platform} script that will captivate viewers and encourage engagement.
"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback to template-based generation
            return await self._generate_fallback_script(transcription, analysis, platform)

    async def _generate_fallback_script(
        self,
        transcription: str,
        analysis: Dict[str, Any],
        platform: str
    ) -> str:
        """Fallback script generation without OpenAI"""
        
        sentences = sent_tokenize(transcription)
        top_keywords = analysis['keywords'][:5]
        
        # Select best sentences
        important_sentences = []
        for sentence in sentences[:20]:  # Limit to first 20 sentences
            if any(keyword.lower() in sentence.lower() for keyword in top_keywords):
                important_sentences.append(sentence)
        
        # Create script structure
        hook = self._select_hook(platform, top_keywords)
        main_content = ' '.join(important_sentences[:3])
        cta = self._select_cta(platform)
        
        return f"{hook}\n\n{main_content}\n\n{cta}"

    def _select_hook(self, platform: str, keywords: List[str]) -> str:
        """Select an appropriate hook for the platform"""
        
        hooks = self.viral_keywords['hooks']
        
        if platform == 'tiktok':
            return f"{hooks[0]} what I discovered about {keywords[0] if keywords else 'this topic'}!"
        elif platform == 'youtube':
            return f"In this video, I'm going to show you {keywords[0] if keywords else 'something amazing'} that most people don't know."
        else:
            return f"{hooks[2]} {keywords[0] if keywords else 'this important topic'}."

    def _select_cta(self, platform: str) -> str:
        """Select an appropriate CTA for the platform"""
        
        ctas = self.viral_keywords['cta_phrases']
        
        if platform == 'tiktok':
            return f"{ctas[0]} in the comments! 👇"
        elif platform == 'youtube':
            return f"If you found this helpful, make sure to subscribe for more content like this. {ctas[1]}!"
        elif platform == 'instagram':
            return f"{ctas[3]} and {ctas[2]}!"
        else:
            return ctas[0]

    async def _generate_hashtags(self, keywords: List[str], platform: str) -> List[str]:
        """Generate relevant hashtags based on keywords and platform"""
        
        hashtags = []
        
        # Add keyword-based hashtags
        for keyword in keywords[:5]:
            hashtag = re.sub(r'[^a-zA-Z0-9]', '', keyword.replace(' ', ''))
            if hashtag:
                hashtags.append(f"#{hashtag}")
        
        # Add platform-specific hashtags
        platform_hashtags = {
            'tiktok': ['#fyp', '#viral', '#trending', '#foryoupage'],
            'youtube': ['#shorts', '#youtube', '#subscribe'],
            'instagram': ['#reels', '#explore', '#viral', '#instagood'],
            'twitter': ['#thread', '#viral', '#trending'],
            'general': ['#viral', '#content', '#trending']
        }
        
        hashtags.extend(platform_hashtags.get(platform, platform_hashtags['general']))
        
        return hashtags[:10]  # Limit to 10 hashtags

    async def _generate_hooks(self, keywords: List[str], platform: str) -> List[str]:
        """Generate multiple hook options"""
        
        base_hooks = self.viral_keywords['hooks']
        generated_hooks = []
        
        for hook_template in base_hooks[:5]:
            if keywords:
                generated_hooks.append(f"{hook_template} {keywords[0]}")
            else:
                generated_hooks.append(hook_template)
        
        return generated_hooks

    async def _generate_ctas(self, platform: str) -> List[str]:
        """Generate multiple CTA options"""
        
        base_ctas = self.viral_keywords['cta_phrases']
        
        if platform == 'tiktok':
            return [
                "Drop a 🔥 if you learned something new!",
                "Comment your biggest takeaway below 👇",
                "Share this with someone who needs to see it!",
                "Follow for more viral content tips!"
            ]
        elif platform == 'youtube':
            return [
                "If this helped you, smash that subscribe button!",
                "Let me know in the comments what you think!",
                "Share this video with someone who needs to see it!",
                "Hit the bell icon for notifications!"
            ]
        else:
            return base_ctas[:4]

    async def _create_timestamps(
        self,
        script_content: str,
        highlights: List[Dict[str, Any]]
    ) -> List[ScriptSection]:
        """Create timestamp alignment between script and video"""
        
        script_sentences = sent_tokenize(script_content)
        timestamps = []
        
        # Map script sentences to video highlights
        for i, sentence in enumerate(script_sentences):
            if i < len(highlights):
                highlight = highlights[i]
                section_type = await self._classify_sentence_type(sentence)
                
                timestamps.append(ScriptSection(
                    start_time=highlight['start_time'],
                    end_time=highlight['end_time'],
                    section_type=section_type,
                    content=sentence,
                    engagement_score=highlight['importance_score'],
                    keywords=await self._extract_sentence_keywords(sentence)
                ))
        
        return timestamps

    async def _extract_sentence_keywords(self, sentence: str) -> List[str]:
        """Extract keywords from a single sentence"""
        
        try:
            keywords = self.keybert.extract_keywords(
                sentence,
                keyphrase_ngram_range=(1, 2),
                stop_words='english',
                top_k=3
            )
            return [kw[0] for kw in keywords]
        except:
            # Fallback to simple word extraction
            words = word_tokenize(sentence.lower())
            stop_words = set(stopwords.words('english'))
            return [word for word in words if word not in stop_words and len(word) > 3][:3]

    async def _calculate_engagement_score(
        self,
        script: str,
        analysis: Dict[str, Any],
        platform: str
    ) -> float:
        """Calculate predicted engagement score for the script"""
        
        score = 0.0
        script_lower = script.lower()
        
        # Sentiment boost
        if analysis['sentiment_score'] > 0:
            score += 0.2
        
        # Keyword density
        keyword_density = sum(1 for keyword in analysis['keywords'][:5] if keyword.lower() in script_lower)
        score += min(keyword_density * 0.1, 0.3)
        
        # Hook presence
        if any(hook.lower() in script_lower for hook in self.viral_keywords['hooks']):
            score += 0.2
        
        # CTA presence
        if any(cta.lower() in script_lower for cta in self.viral_keywords['cta_phrases']):
            score += 0.15
        
        # Question presence (engagement)
        question_count = script.count('?')
        score += min(question_count * 0.05, 0.15)
        
        # Platform-specific bonuses
        if platform == 'tiktok' and len(script.split()) < 100:
            score += 0.1  # Brevity bonus for TikTok
        elif platform == 'youtube' and 100 <= len(script.split()) <= 200:
            score += 0.1  # Optimal length for YouTube Shorts
        
        return min(score, 1.0)

    async def _generate_title(self, keywords: List[str], platform: str) -> str:
        """Generate an engaging title for the script"""
        
        if not keywords:
            return f"Viral {platform.title()} Script"
        
        title_templates = [
            f"The Truth About {keywords[0].title()}",
            f"How {keywords[0].title()} Changed Everything",
            f"Why Everyone's Talking About {keywords[0].title()}",
            f"The {keywords[0].title()} Secret Nobody Tells You",
            f"This {keywords[0].title()} Trick Will Blow Your Mind"
        ]
        
        # Select template based on sentiment
        import random
        return random.choice(title_templates)

class ScriptOptimizer:
    """Optimize existing scripts for better engagement"""
    
    def __init__(self):
        self.generator = ScriptGenerator()
    
    async def optimize_script(
        self,
        original_script: str,
        target_platform: str,
        optimization_goals: List[str] = None
    ) -> Dict[str, Any]:
        """Optimize an existing script for better performance"""
        
        if optimization_goals is None:
            optimization_goals = ['engagement', 'virality', 'platform_fit']
        
        optimizations = {}
        
        # Analyze current script
        analysis = await self.generator._analyze_transcription(original_script)
        current_score = await self.generator._calculate_engagement_score(
            original_script, analysis, target_platform
        )
        
        # Suggest improvements
        suggestions = []
        
        # Hook improvement
        if not any(hook.lower() in original_script.lower() for hook in self.generator.viral_keywords['hooks']):
            suggestions.append({
                'type': 'hook',
                'suggestion': 'Add a stronger opening hook',
                'example': await self.generator._select_hook(target_platform, analysis['keywords'])
            })
        
        # CTA improvement
        if not any(cta.lower() in original_script.lower() for cta in self.generator.viral_keywords['cta_phrases']):
            suggestions.append({
                'type': 'cta',
                'suggestion': 'Add a call-to-action',
                'example': await self.generator._select_cta(target_platform)
            })
        
        # Keyword optimization
        keyword_density = sum(1 for keyword in analysis['keywords'][:5] if keyword.lower() in original_script.lower())
        if keyword_density < 2:
            suggestions.append({
                'type': 'keywords',
                'suggestion': f"Include more relevant keywords: {', '.join(analysis['keywords'][:3])}",
                'example': f"Try incorporating: {analysis['keywords'][0]}"
            })
        
        return {
            'current_score': current_score,
            'optimized_score_potential': min(current_score + len(suggestions) * 0.1, 1.0),
            'suggestions': suggestions,
            'recommended_hashtags': await self.generator._generate_hashtags(analysis['keywords'], target_platform)
        }

# Usage example and testing
async def test_script_generation():
    """Test the script generation functionality"""
    
    generator = ScriptGenerator()
    
    sample_transcription = """
    Today I want to talk about the secret to viral content that nobody really discusses. 
    Most people think it's about luck, but there's actually a science behind it. 
    The first thing you need to understand is that attention spans are getting shorter every day.
    So your hook needs to be absolutely incredible. You have about 3 seconds to capture someone's attention.
    After that, you need to deliver value quickly and keep them engaged throughout the entire video.
    The key is to create moments of surprise and revelation that keep people watching until the end.
    """
    
    script = await generator.generate_script(
        transcription_text=sample_transcription,
        video_duration=60.0,
        platform='tiktok',
        include_timestamps=True
    )
    
    print(f"Generated Script Title: {script.title}")
    print(f"Platform: {script.platform_optimization}")
    print(f"Engagement Score: {script.engagement_score:.2f}")
    print(f"Content: {script.content}")
    print(f"Hashtags: {', '.join(script.hashtags)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_script_generation())
