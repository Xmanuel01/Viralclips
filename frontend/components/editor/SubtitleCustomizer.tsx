'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { HexColorPicker } from 'react-colorful';
import Slider from 'react-slider';
import Select from 'react-select';
import {
  PaintBrushIcon,
  EyeIcon,
  SwatchIcon,
  AdjustmentsHorizontalIcon,
  PlayIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

import { SubtitleConfig, SubtitleCustomizerProps } from '../../../shared/types';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Tooltip } from '../ui/Tooltip';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';

const FONT_OPTIONS = [
  { value: 'Inter', label: 'Inter (Modern)' },
  { value: 'Montserrat', label: 'Montserrat (Trendy)' },
  { value: 'Roboto', label: 'Roboto (Clean)' },
  { value: 'Oswald', label: 'Oswald (Bold)' },
  { value: 'Source Sans Pro', label: 'Source Sans (Readable)' },
  { value: 'Poppins', label: 'Poppins (Friendly)' },
  { value: 'Open Sans', label: 'Open Sans (Professional)' },
  { value: 'Lato', label: 'Lato (Elegant)' },
  { value: 'Nunito', label: 'Nunito (Rounded)' },
  { value: 'Playfair Display', label: 'Playfair (Luxury)' }
];

const ANIMATION_OPTIONS = [
  { value: 'none', label: 'No Animation', preview: 'Static text' },
  { value: 'fade', label: 'Fade In', preview: 'Gentle appearance' },
  { value: 'bounce', label: 'Bounce', preview: 'Playful entrance' },
  { value: 'slide', label: 'Slide Up', preview: 'Smooth upward motion' },
  { value: 'pulse', label: 'Pulse', preview: 'Rhythmic scaling' },
  { value: 'typewriter', label: 'Typewriter', preview: 'Character by character' }
];

const POSITION_OPTIONS = [
  { value: 'top', label: 'Top', icon: '⬆️' },
  { value: 'center', label: 'Center', icon: '◯' },
  { value: 'bottom', label: 'Bottom', icon: '⬇️' }
];

const PRESET_STYLES = [
  {
    name: 'Modern Minimal',
    config: {
      font: 'Inter',
      size: 24,
      color: '#FFFFFF',
      background: 'rgba(0,0,0,0.8)',
      animation: 'fade',
      position: 'bottom'
    }
  },
  {
    name: 'Vibrant Pop',
    config: {
      font: 'Montserrat',
      size: 28,
      color: '#FF6B6B',
      background: 'rgba(255,255,255,0.9)',
      animation: 'bounce',
      position: 'center'
    }
  },
  {
    name: 'Business Pro',
    config: {
      font: 'Roboto',
      size: 22,
      color: '#2C3E50',
      background: 'rgba(255,255,255,0.95)',
      animation: 'slide',
      position: 'bottom'
    }
  },
  {
    name: 'Fitness Energy',
    config: {
      font: 'Oswald',
      size: 26,
      color: '#00D4AA',
      background: 'rgba(0,0,0,0.7)',
      animation: 'pulse',
      position: 'top'
    }
  }
];

export function SubtitleCustomizer({
  config,
  onChange,
  previewText = 'This is a sample subtitle text to preview your styling choices.'
}: SubtitleCustomizerProps) {
  const [localConfig, setLocalConfig] = useState<SubtitleConfig>(config);
  const [showColorPicker, setShowColorPicker] = useState<'text' | 'background' | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  const handleConfigChange = (updates: Partial<SubtitleConfig>) => {
    const newConfig = { ...localConfig, ...updates };
    setLocalConfig(newConfig);
    onChange(newConfig);
  };

  const applyPreset = (preset: typeof PRESET_STYLES[0]) => {
    handleConfigChange(preset.config);
  };

  const triggerAnimation = () => {
    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 1000);
  };

  const parseColor = (colorString: string) => {
    if (colorString.startsWith('rgba')) {
      const match = colorString.match(/rgba?\(([^)]+)\)/);
      if (match) {
        const values = match[1].split(',').map(v => v.trim());
        if (values.length >= 3) {
          const r = parseInt(values[0]);
          const g = parseInt(values[1]);
          const b = parseInt(values[2]);
          return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
        }
      }
    }
    return colorString;
  };

  const createRgbaColor = (hex: string, opacity: number) => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${opacity})`;
  };

  const getBackgroundOpacity = (background: string) => {
    const match = background.match(/rgba?\([^,]+,[^,]+,[^,]+,([^)]+)\)/);
    return match ? parseFloat(match[1]) : 0.8;
  };

  const getBackgroundColor = (background: string) => {
    const match = background.match(/rgba?\(([^,]+),([^,]+),([^,]+)/);
    if (match) {
      const r = parseInt(match[1]);
      const g = parseInt(match[2]);
      const b = parseInt(match[3]);
      return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }
    return '#000000';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Controls Panel */}
      <Card className="h-fit">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <PaintBrushIcon className="h-5 w-5 text-gray-500" />
            <h3 className="text-lg font-semibold">Subtitle Customizer</h3>
          </div>
        </div>

        <div className="p-4 space-y-6">
          {/* Preset Styles */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Quick Presets
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {PRESET_STYLES.map((preset, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => applyPreset(preset)}
                  className="justify-start text-left h-auto p-3"
                >
                  <div>
                    <div className="font-medium text-xs">{preset.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {preset.config.font} • {preset.config.animation}
                    </div>
                  </div>
                </Button>
              ))}
            </div>
          </div>

          <Tabs defaultValue="typography" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="typography">Typography</TabsTrigger>
              <TabsTrigger value="colors">Colors</TabsTrigger>
              <TabsTrigger value="effects">Effects</TabsTrigger>
            </TabsList>

            {/* Typography Tab */}
            <TabsContent value="typography" className="space-y-4">
              {/* Font Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Font Family
                </label>
                <Select
                  value={FONT_OPTIONS.find(f => f.value === localConfig.font)}
                  onChange={(option) => handleConfigChange({ font: option?.value })}
                  options={FONT_OPTIONS}
                  className="react-select-container"
                  classNamePrefix="react-select"
                />
              </div>

              {/* Font Size */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Font Size: {localConfig.size}px
                </label>
                <Slider
                  value={[localConfig.size || 24]}
                  onAfterChange={([value]) => handleConfigChange({ size: value })}
                  min={12}
                  max={72}
                  step={2}
                  className="subtitle-slider"
                  thumbClassName="subtitle-slider-thumb"
                  trackClassName="subtitle-slider-track"
                />
              </div>

              {/* Position */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Position
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {POSITION_OPTIONS.map((pos) => (
                    <Button
                      key={pos.value}
                      variant={localConfig.position === pos.value ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => handleConfigChange({ position: pos.value })}
                      className="flex items-center space-x-2"
                    >
                      <span>{pos.icon}</span>
                      <span>{pos.label}</span>
                    </Button>
                  ))}
                </div>
              </div>
            </TabsContent>

            {/* Colors Tab */}
            <TabsContent value="colors" className="space-y-4">
              {/* Text Color */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Text Color
                </label>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => setShowColorPicker(showColorPicker === 'text' ? null : 'text')}
                    className="w-10 h-10 rounded-lg border-2 border-gray-300 flex items-center justify-center"
                    style={{ backgroundColor: localConfig.color }}
                  >
                    <SwatchIcon className="h-5 w-5 text-white drop-shadow" />
                  </button>
                  <input
                    type="text"
                    value={localConfig.color}
                    onChange={(e) => handleConfigChange({ color: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:border-gray-600 dark:bg-gray-800"
                  />
                </div>
                
                {showColorPicker === 'text' && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="mt-3"
                  >
                    <HexColorPicker
                      color={localConfig.color}
                      onChange={(color) => handleConfigChange({ color })}
                    />
                  </motion.div>
                )}
              </div>

              {/* Background Color */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Background
                </label>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => setShowColorPicker(showColorPicker === 'background' ? null : 'background')}
                      className="w-10 h-10 rounded-lg border-2 border-gray-300 flex items-center justify-center"
                      style={{ backgroundColor: getBackgroundColor(localConfig.background || 'rgba(0,0,0,0.8)') }}
                    >
                      <SwatchIcon className="h-5 w-5 text-white drop-shadow" />
                    </button>
                    <div className="flex-1">
                      <label className="block text-xs text-gray-500 mb-1">
                        Opacity: {Math.round(getBackgroundOpacity(localConfig.background || 'rgba(0,0,0,0.8)') * 100)}%
                      </label>
                      <Slider
                        value={[getBackgroundOpacity(localConfig.background || 'rgba(0,0,0,0.8)') * 100]}
                        onAfterChange={([value]) => {
                          const bgColor = getBackgroundColor(localConfig.background || 'rgba(0,0,0,0.8)');
                          const newBackground = createRgbaColor(bgColor, value / 100);
                          handleConfigChange({ background: newBackground });
                        }}
                        min={0}
                        max={100}
                        step={5}
                        className="subtitle-slider"
                        thumbClassName="subtitle-slider-thumb"
                        trackClassName="subtitle-slider-track"
                      />
                    </div>
                  </div>
                  
                  {showColorPicker === 'background' && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="mt-3"
                    >
                      <HexColorPicker
                        color={getBackgroundColor(localConfig.background || 'rgba(0,0,0,0.8)')}
                        onChange={(color) => {
                          const opacity = getBackgroundOpacity(localConfig.background || 'rgba(0,0,0,0.8)');
                          const newBackground = createRgbaColor(color, opacity);
                          handleConfigChange({ background: newBackground });
                        }}
                      />
                    </motion.div>
                  )}
                </div>
              </div>

              {/* Quick Color Presets */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Color Presets
                </label>
                <div className="grid grid-cols-6 gap-2">
                  {[
                    { text: '#FFFFFF', bg: 'rgba(0,0,0,0.8)', name: 'Classic' },
                    { text: '#000000', bg: 'rgba(255,255,255,0.9)', name: 'Inverse' },
                    { text: '#FF6B6B', bg: 'rgba(255,255,255,0.9)', name: 'Red Pop' },
                    { text: '#4ECDC4', bg: 'rgba(0,0,0,0.8)', name: 'Mint' },
                    { text: '#45B7D1', bg: 'rgba(255,255,255,0.9)', name: 'Ocean' },
                    { text: '#F39C12', bg: 'rgba(0,0,0,0.8)', name: 'Gold' }
                  ].map((preset, index) => (
                    <Tooltip key={index} content={preset.name}>
                      <button
                        onClick={() => handleConfigChange({
                          color: preset.text,
                          background: preset.bg
                        })}
                        className="w-8 h-8 rounded-lg border-2 border-gray-300 relative overflow-hidden"
                        style={{ backgroundColor: preset.bg }}
                      >
                        <div
                          className="absolute inset-1 rounded flex items-center justify-center text-xs font-bold"
                          style={{ color: preset.text }}
                        >
                          A
                        </div>
                      </button>
                    </Tooltip>
                  ))}
                </div>
              </div>
            </TabsContent>

            {/* Effects Tab */}
            <TabsContent value="effects" className="space-y-4">
              {/* Animation */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Animation Style
                </label>
                <div className="space-y-2">
                  {ANIMATION_OPTIONS.map((animation) => (
                    <div
                      key={animation.value}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        localConfig.animation === animation.value
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 hover:border-gray-300 dark:border-gray-600'
                      }`}
                      onClick={() => handleConfigChange({ animation: animation.value })}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-sm">{animation.label}</div>
                          <div className="text-xs text-gray-500">{animation.preview}</div>
                        </div>
                        {localConfig.animation === animation.value && (
                          <Badge variant="default" size="xs">Selected</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Animation Test */}
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Test Animation
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={triggerAnimation}
                  disabled={localConfig.animation === 'none'}
                >
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Preview
                </Button>
              </div>
            </TabsContent>
          </Tabs>

          {/* Reset Button */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleConfigChange({
                font: 'Inter',
                size: 24,
                color: '#FFFFFF',
                background: 'rgba(0,0,0,0.8)',
                animation: 'fade',
                position: 'bottom'
              })}
              className="w-full"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Reset to Default
            </Button>
          </div>
        </div>
      </Card>

      {/* Live Preview Panel */}
      <Card className="h-fit">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <EyeIcon className="h-5 w-5 text-gray-500" />
              <h3 className="text-lg font-semibold">Live Preview</h3>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={triggerAnimation}
            >
              <PlayIcon className="h-4 w-4 mr-2" />
              Test
            </Button>
          </div>
        </div>

        <div className="p-4">
          {/* Preview Container */}
          <div className="relative aspect-video bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg overflow-hidden">
            {/* Mock Video Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/20 to-purple-600/20" />
            
            {/* Subtitle Preview */}
            <motion.div
              key={isAnimating ? 'animating' : 'static'}
              initial={getAnimationInitial(localConfig.animation || 'fade')}
              animate={getAnimationAnimate(localConfig.animation || 'fade')}
              className={`absolute ${getPositionClasses(localConfig.position || 'bottom')} z-10`}
              style={{
                fontFamily: localConfig.font || 'Inter',
                fontSize: `${localConfig.size || 24}px`,
                color: localConfig.color || '#FFFFFF',
                backgroundColor: localConfig.background || 'rgba(0,0,0,0.8)',
                padding: '8px 16px',
                borderRadius: '8px',
                textAlign: 'center',
                fontWeight: '600',
                lineHeight: '1.2',
                maxWidth: '80%'
              }}
            >
              {previewText}
            </motion.div>
          </div>

          {/* Preview Info */}
          <div className="mt-4 space-y-2">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Font:</span>
                <span className="ml-2 font-medium">{localConfig.font}</span>
              </div>
              <div>
                <span className="text-gray-500">Size:</span>
                <span className="ml-2 font-medium">{localConfig.size}px</span>
              </div>
              <div>
                <span className="text-gray-500">Animation:</span>
                <span className="ml-2 font-medium capitalize">{localConfig.animation}</span>
              </div>
              <div>
                <span className="text-gray-500">Position:</span>
                <span className="ml-2 font-medium capitalize">{localConfig.position}</span>
              </div>
            </div>
            
            {/* Style Code */}
            <details className="mt-4">
              <summary className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer">
                View CSS Code
              </summary>
              <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-x-auto">
{`font-family: '${localConfig.font}', sans-serif;
font-size: ${localConfig.size}px;
color: ${localConfig.color};
background: ${localConfig.background};
animation: ${localConfig.animation};
position: ${localConfig.position};`}
              </pre>
            </details>
          </div>
        </div>
      </Card>
    </div>
  );
}

// Animation helper functions
function getAnimationInitial(animation: string) {
  switch (animation) {
    case 'fade':
      return { opacity: 0 };
    case 'bounce':
      return { opacity: 0, scale: 0.5 };
    case 'slide':
      return { opacity: 0, y: 20 };
    case 'pulse':
      return { opacity: 0, scale: 0.8 };
    case 'typewriter':
      return { opacity: 1, width: 0 };
    default:
      return { opacity: 1 };
  }
}

function getAnimationAnimate(animation: string) {
  switch (animation) {
    case 'fade':
      return { opacity: 1, transition: { duration: 0.5 } };
    case 'bounce':
      return { 
        opacity: 1, 
        scale: 1, 
        transition: { 
          type: 'spring',
          stiffness: 300,
          damping: 10
        } 
      };
    case 'slide':
      return { 
        opacity: 1, 
        y: 0, 
        transition: { 
          type: 'spring',
          stiffness: 200,
          damping: 20
        } 
      };
    case 'pulse':
      return { 
        opacity: 1, 
        scale: [0.8, 1.1, 1], 
        transition: { 
          duration: 0.6,
          times: [0, 0.5, 1]
        } 
      };
    case 'typewriter':
      return { 
        width: 'auto', 
        transition: { 
          duration: 1,
          ease: 'linear'
        } 
      };
    default:
      return { opacity: 1 };
  }
}

function getPositionClasses(position: string): string {
  switch (position) {
    case 'top':
      return 'top-4 left-1/2 transform -translate-x-1/2';
    case 'center':
      return 'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2';
    case 'bottom':
    default:
      return 'bottom-4 left-1/2 transform -translate-x-1/2';
  }
}

// Helper functions from previous component
function parseColor(colorString: string) {
  if (colorString.startsWith('rgba')) {
    const match = colorString.match(/rgba?\(([^)]+)\)/);
    if (match) {
      const values = match[1].split(',').map(v => v.trim());
      if (values.length >= 3) {
        const r = parseInt(values[0]);
        const g = parseInt(values[1]);
        const b = parseInt(values[2]);
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
      }
    }
  }
  return colorString;
}

function createRgbaColor(hex: string, opacity: number) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${opacity})`;
}

function getBackgroundOpacity(background: string) {
  const match = background.match(/rgba?\([^,]+,[^,]+,[^,]+,([^)]+)\)/);
  return match ? parseFloat(match[1]) : 0.8;
}

function getBackgroundColor(background: string) {
  const match = background.match(/rgba?\(([^,]+),([^,]+),([^,]+)/);
  if (match) {
    const r = parseInt(match[1]);
    const g = parseInt(match[2]);
    const b = parseInt(match[3]);
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }
  return '#000000';
}
