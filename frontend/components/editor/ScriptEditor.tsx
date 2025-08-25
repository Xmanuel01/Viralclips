'use client';

import React, { useState, useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Highlight from '@tiptap/extension-highlight';
import CharacterCount from '@tiptap/extension-character-count';
import Placeholder from '@tiptap/extension-placeholder';
import { motion, AnimatePresence } from 'framer-motion';
import {
  SparklesIcon,
  ClockIcon,
  StarIcon,
  HashtagIcon,
  MegaphoneIcon,
  EyeIcon,
  DocumentTextIcon,
  ChevronDownIcon,
  PlayIcon,
  PauseIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';

import { Script, Video, Platform, ScriptEditorProps } from '../../../shared/types';
import { Button } from '../ui/Button';
import { Select } from '../ui/Select';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Tooltip } from '../ui/Tooltip';
import { VideoPreview } from './VideoPreview';

const PLATFORMS: { value: Platform; label: string; icon: string }[] = [
  { value: 'tiktok', label: 'TikTok', icon: '🎵' },
  { value: 'youtube', label: 'YouTube Shorts', icon: '📺' },
  { value: 'instagram', label: 'Instagram Reels', icon: '📸' },
  { value: 'twitter', label: 'Twitter/X', icon: '🐦' },
  { value: 'general', label: 'General', icon: '🌐' }
];

export function ScriptEditor({
  script,
  video,
  onSave,
  onGenerate,
  isGenerating = false
}: ScriptEditorProps) {
  const [title, setTitle] = useState(script?.title || '');
  const [platform, setPlatform] = useState<Platform>(script?.platform_optimization || 'general');
  const [customPrompt, setCustomPrompt] = useState('');
  const [includeTimestamps, setIncludeTimestamps] = useState(true);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [selectedTimestamp, setSelectedTimestamp] = useState<number | null>(null);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Highlight.configure({ multicolor: true }),
      CharacterCount.configure({ limit: 2000 }),
      Placeholder.configure({
        placeholder: isGenerating ? 'Generating your script...' : 'Start writing your script or generate one using AI...'
      })
    ],
    content: script?.content || '',
    editable: !isGenerating,
    onUpdate: ({ editor }) => {
      // Auto-save functionality could be added here
    }
  });

  useEffect(() => {
    if (script?.content && editor) {
      editor.commands.setContent(script.content);
    }
  }, [script?.content, editor]);

  const handleGenerate = () => {
    if (!video?.id) return;
    
    onGenerate({
      video_id: video.id,
      platform_optimization: platform,
      custom_prompt: customPrompt || undefined,
      include_timestamps: includeTimestamps
    });
  };

  const handleSave = () => {
    if (!editor) return;
    
    const content = editor.getHTML();
    onSave({
      title,
      content,
      platform_optimization: platform
    });
  };

  const getEngagementColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatScore = (score: number) => {
    return (score * 100).toFixed(0);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      {/* Editor Panel */}
      <Card className="flex flex-col h-full">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <DocumentTextIcon className="h-5 w-5 text-gray-500" />
            <h3 className="text-lg font-semibold">Script Editor</h3>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPreviewMode(!isPreviewMode)}
            >
              <EyeIcon className="h-4 w-4" />
              {isPreviewMode ? 'Edit' : 'Preview'}
            </Button>
          </div>
        </div>

        <div className="flex-1 flex flex-col p-4 space-y-4">
          {/* Script Header */}
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Script title..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:border-gray-600 dark:bg-gray-800"
            />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Select
                label="Platform"
                value={platform}
                onChange={(value) => setPlatform(value as Platform)}
                options={PLATFORMS.map(p => ({
                  value: p.value,
                  label: `${p.icon} ${p.label}`
                }))}
              />
              
              {script && (
                <div className="flex items-center space-x-4">
                  <Tooltip content="Engagement Score">
                    <div className="flex items-center space-x-1">
                      <StarIcon className={`h-4 w-4 ${getEngagementColor(script.engagement_score)}`} />
                      <span className={`text-sm font-medium ${getEngagementColor(script.engagement_score)}`}>
                        {formatScore(script.engagement_score)}%
                      </span>
                    </div>
                  </Tooltip>
                  
                  <Tooltip content="Sentiment Score">
                    <div className="flex items-center space-x-1">
                      <div className={`w-2 h-2 rounded-full ${
                        script.sentiment_score > 0.2 ? 'bg-green-500' :
                        script.sentiment_score < -0.2 ? 'bg-red-500' : 'bg-yellow-500'
                      }`} />
                      <span className="text-sm text-gray-600">
                        {script.sentiment_score > 0.2 ? 'Positive' :
                         script.sentiment_score < -0.2 ? 'Negative' : 'Neutral'}
                      </span>
                    </div>
                  </Tooltip>
                </div>
              )}
            </div>
          </div>

          {/* AI Generation Controls */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg p-4 space-y-3"
          >
            <div className="flex items-center space-x-2">
              <SparklesIcon className="h-5 w-5 text-purple-600" />
              <h4 className="font-medium text-purple-900 dark:text-purple-100">AI Script Generation</h4>
            </div>
            
            <textarea
              placeholder="Optional: Add custom instructions for script generation..."
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none dark:border-purple-700 dark:bg-purple-900/20"
            />
            
            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={includeTimestamps}
                  onChange={(e) => setIncludeTimestamps(e.target.checked)}
                  className="rounded border-purple-300 text-purple-600 focus:ring-purple-500"
                />
                <span>Include timestamps</span>
                <ClockIcon className="h-4 w-4 text-purple-500" />
              </label>
              
              <Button
                onClick={handleGenerate}
                disabled={isGenerating || !video?.id}
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Generating...
                  </>
                ) : (
                  <>
                    <SparklesIcon className="h-4 w-4 mr-2" />
                    Generate Script
                  </>
                )}
              </Button>
            </div>
          </motion.div>

          {/* Editor */}
          <div className="flex-1 border border-gray-200 rounded-lg dark:border-gray-700">
            <div className="border-b border-gray-200 dark:border-gray-700 p-2">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => editor?.chain().focus().toggleBold().run()}
                  className={`p-2 rounded ${
                    editor?.isActive('bold') ? 'bg-gray-200 dark:bg-gray-700' : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <strong>B</strong>
                </button>
                <button
                  onClick={() => editor?.chain().focus().toggleItalic().run()}
                  className={`p-2 rounded ${
                    editor?.isActive('italic') ? 'bg-gray-200 dark:bg-gray-700' : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <em>I</em>
                </button>
                <button
                  onClick={() => editor?.chain().focus().toggleHighlight().run()}
                  className={`p-2 rounded ${
                    editor?.isActive('highlight') ? 'bg-yellow-200 dark:bg-yellow-700' : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <span className="bg-yellow-200 px-1">H</span>
                </button>
              </div>
            </div>
            
            <div className="flex-1 p-4 min-h-[300px]">
              <EditorContent 
                editor={editor} 
                className="prose prose-sm max-w-none focus:outline-none dark:prose-invert"
              />
            </div>
            
            {editor && (
              <div className="border-t border-gray-200 dark:border-gray-700 p-2 text-xs text-gray-500 flex justify-between">
                <span>
                  {editor.storage.characterCount.characters()} characters
                </span>
                <span>
                  {editor.storage.characterCount.words()} words
                </span>
              </div>
            )}
          </div>

          {/* Script Insights */}
          {script && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-3"
            >
              <h5 className="font-medium text-gray-900 dark:text-gray-100">Script Insights</h5>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg text-center">
                  <StarIcon className="h-5 w-5 text-blue-600 mx-auto mb-1" />
                  <div className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    {formatScore(script.engagement_score)}%
                  </div>
                  <div className="text-xs text-blue-600">Engagement</div>
                </div>
                
                <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg text-center">
                  <HashtagIcon className="h-5 w-5 text-green-600 mx-auto mb-1" />
                  <div className="text-sm font-medium text-green-900 dark:text-green-100">
                    {script.keywords.length}
                  </div>
                  <div className="text-xs text-green-600">Keywords</div>
                </div>
                
                <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg text-center">
                  <MegaphoneIcon className="h-5 w-5 text-purple-600 mx-auto mb-1" />
                  <div className="text-sm font-medium text-purple-900 dark:text-purple-100">
                    {script.hooks.length}
                  </div>
                  <div className="text-xs text-purple-600">Hooks</div>
                </div>
                
                <div className="bg-orange-50 dark:bg-orange-900/20 p-3 rounded-lg text-center">
                  <ClockIcon className="h-5 w-5 text-orange-600 mx-auto mb-1" />
                  <div className="text-sm font-medium text-orange-900 dark:text-orange-100">
                    {script.timestamps.length}
                  </div>
                  <div className="text-xs text-orange-600">Timestamps</div>
                </div>
              </div>
              
              {/* Keywords */}
              {script.keywords.length > 0 && (
                <div>
                  <h6 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Keywords</h6>
                  <div className="flex flex-wrap gap-1">
                    {script.keywords.slice(0, 8).map((keyword, index) => (
                      <Badge key={index} variant="secondary" size="sm">
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Hashtags */}
              {script.hashtags.length > 0 && (
                <div>
                  <h6 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Suggested Hashtags</h6>
                  <div className="flex flex-wrap gap-1">
                    {script.hashtags.slice(0, 6).map((hashtag, index) => (
                      <Badge key={index} variant="outline" size="sm" className="text-blue-600">
                        {hashtag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Hooks */}
              {script.hooks.length > 0 && (
                <div>
                  <h6 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Hook Options</h6>
                  <div className="space-y-2">
                    {script.hooks.slice(0, 3).map((hook, index) => (
                      <div
                        key={index}
                        className="p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        onClick={() => {
                          if (editor) {
                            editor.commands.insertContent(`${hook} `);
                          }
                        }}
                      >
                        {hook}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => editor?.commands.undo()}
                disabled={!editor?.can().undo()}
              >
                Undo
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => editor?.commands.redo()}
                disabled={!editor?.can().redo()}
              >
                Redo
              </Button>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                onClick={() => {/* Export functionality */}}
              >
                Export
              </Button>
              <Button
                onClick={handleSave}
                disabled={!title.trim() || !editor?.getText().trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Save Script
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Preview Panel */}
      <Card className="flex flex-col h-full">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <PlayIcon className="h-5 w-5 text-gray-500" />
            <h3 className="text-lg font-semibold">Live Preview</h3>
            {platform !== 'general' && (
              <Badge variant="outline" size="sm">
                {PLATFORMS.find(p => p.value === platform)?.icon} {platform}
              </Badge>
            )}
          </div>
        </div>

        <div className="flex-1 p-4">
          {video && (
            <div className="space-y-4">
              {/* Video Preview */}
              <VideoPreview
                video={video}
                selectedTimestamp={selectedTimestamp}
                onTimeUpdate={(time) => setSelectedTimestamp(time)}
                aspectRatio="9:16"
                showControls={true}
              />
              
              {/* Script Timestamps */}
              {script?.timestamps && script.timestamps.length > 0 && (
                <div className="space-y-2">
                  <h6 className="text-sm font-medium text-gray-700 dark:text-gray-300">Script Timeline</h6>
                  <div className="max-h-40 overflow-y-auto space-y-1">
                    {script.timestamps.map((timestamp, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className={`p-2 rounded-lg cursor-pointer transition-colors ${
                          selectedTimestamp !== null &&
                          selectedTimestamp >= timestamp.start_time &&
                          selectedTimestamp <= timestamp.end_time
                            ? 'bg-blue-100 dark:bg-blue-900/30 border border-blue-300 dark:border-blue-700'
                            : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                        onClick={() => setSelectedTimestamp(timestamp.start_time)}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-mono text-gray-500">
                            {formatTime(timestamp.start_time)} - {formatTime(timestamp.end_time)}
                          </span>
                          <Badge 
                            variant="outline" 
                            size="xs"
                            className={getTimestampTypeColor(timestamp.section_type)}
                          >
                            {timestamp.section_type}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
                          {timestamp.content}
                        </p>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {!video && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <PlayIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Upload a video to see the preview</p>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

// Helper functions
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function getTimestampTypeColor(type: string): string {
  const colors = {
    hook: 'border-red-300 text-red-700 bg-red-50',
    content: 'border-blue-300 text-blue-700 bg-blue-50',
    cta: 'border-green-300 text-green-700 bg-green-50',
    transition: 'border-purple-300 text-purple-700 bg-purple-50'
  };
  return colors[type as keyof typeof colors] || 'border-gray-300 text-gray-700 bg-gray-50';
}
