'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  StarIcon,
  PlayIcon,
  PlusIcon,
  HeartIcon,
  EyeIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon, HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';

import { Template, TemplateType, TemplateGalleryProps } from '../../../shared/types';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Select } from '../ui/Select';
import { Input } from '../ui/Input';
import { Tooltip } from '../ui/Tooltip';
import { Modal } from '../ui/Modal';
import { TemplatePreview } from './TemplatePreview';

const TEMPLATE_CATEGORIES = [
  { value: 'all', label: 'All Categories', icon: '🌐' },
  { value: 'general', label: 'General', icon: '📄' },
  { value: 'business', label: 'Business', icon: '💼' },
  { value: 'entertainment', label: 'Entertainment', icon: '🎭' },
  { value: 'education', label: 'Education', icon: '📚' },
  { value: 'fitness', label: 'Fitness', icon: '💪' },
  { value: 'lifestyle', label: 'Lifestyle', icon: '✨' },
  { value: 'tech', label: 'Technology', icon: '💻' },
  { value: 'food', label: 'Food & Cooking', icon: '🍳' },
  { value: 'travel', label: 'Travel', icon: '✈️' },
  { value: 'gaming', label: 'Gaming', icon: '🎮' }
];

const TEMPLATE_TYPES = [
  { value: 'all', label: 'All Types' },
  { value: 'subtitle', label: 'Subtitle Templates' },
  { value: 'video', label: 'Video Templates' },
  { value: 'brand', label: 'Brand Templates' }
];

export function TemplateGallery({
  category,
  type,
  selectedTemplate,
  onSelectTemplate,
  showUserTemplates = true
}: TemplateGalleryProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(category || 'all');
  const [selectedType, setSelectedType] = useState<string>(type || 'all');
  const [showFilters, setShowFilters] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [view, setView] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    fetchTemplates();
  }, [selectedCategory, selectedType, showUserTemplates]);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: '1',
        page_size: '50',
        include_system: 'true',
        include_user: showUserTemplates.toString()
      });

      if (selectedCategory !== 'all') {
        params.append('category', selectedCategory);
      }
      if (selectedType !== 'all') {
        params.append('type', selectedType);
      }

      const response = await fetch(`/api/templates?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setTemplates(data.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTemplates = templates.filter(template =>
    template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const toggleFavorite = (templateId: string) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(templateId)) {
      newFavorites.delete(templateId);
    } else {
      newFavorites.add(templateId);
    }
    setFavorites(newFavorites);
    // In a real app, this would sync with the backend
  };

  const handleTemplateSelect = (template: Template) => {
    onSelectTemplate(template);
  };

  const renderRating = (rating: number) => {
    return (
      <div className="flex items-center space-x-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <StarSolidIcon
            key={star}
            className={`h-3 w-3 ${
              star <= rating ? 'text-yellow-400' : 'text-gray-300'
            }`}
          />
        ))}
        <span className="text-xs text-gray-500 ml-1">({rating.toFixed(1)})</span>
      </div>
    );
  };

  const getTemplateTypeIcon = (templateType: TemplateType) => {
    const icons = {
      subtitle: '💬',
      video: '🎬',
      brand: '🏷️'
    };
    return icons[templateType] || '📄';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Template Gallery
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Choose from professional templates to enhance your clips
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <FunnelIcon className="h-4 w-4 mr-2" />
            Filters
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setView(view === 'grid' ? 'list' : 'grid')}
          >
            {view === 'grid' ? '📋' : '📊'}
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="space-y-4">
        {/* Search */}
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <Input
            type="text"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Filters */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
            >
              <Select
                label="Category"
                value={selectedCategory}
                onChange={setSelectedCategory}
                options={TEMPLATE_CATEGORIES.map(cat => ({
                  value: cat.value,
                  label: `${cat.icon} ${cat.label}`
                }))}
              />
              
              <Select
                label="Type"
                value={selectedType}
                onChange={setSelectedType}
                options={TEMPLATE_TYPES}
              />
              
              <div className="flex items-end">
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={showUserTemplates}
                    onChange={(e) => {
                      // This would trigger a prop update in the parent component
                      fetchTemplates();
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Include my templates</span>
                </label>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Templates Grid/List */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, index) => (
            <Card key={index} className="animate-pulse">
              <div className="aspect-video bg-gray-200 dark:bg-gray-700 rounded-t-lg" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded" />
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <motion.div 
          layout
          className={view === 'grid' 
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
            : "space-y-4"
          }
        >
          <AnimatePresence>
            {filteredTemplates.map((template) => (
              <motion.div
                key={template.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                whileHover={{ y: -2 }}
                className={view === 'list' ? 'w-full' : ''}
              >
                <Card 
                  className={`relative overflow-hidden cursor-pointer transition-all duration-200 hover:shadow-lg ${
                    selectedTemplate === template.id 
                      ? 'ring-2 ring-blue-500 shadow-lg' 
                      : 'hover:shadow-md'
                  } ${view === 'list' ? 'flex' : ''}`}
                  onClick={() => handleTemplateSelect(template)}
                >
                  {/* Premium Badge */}
                  {template.is_premium && (
                    <div className="absolute top-2 left-2 z-10">
                      <Badge variant="premium" size="sm">
                        <SparklesIcon className="h-3 w-3 mr-1" />
                        Pro
                      </Badge>
                    </div>
                  )}

                  {/* Favorite Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFavorite(template.id);
                    }}
                    className="absolute top-2 right-2 z-10 p-1 rounded-full bg-white/80 hover:bg-white transition-colors"
                  >
                    {favorites.has(template.id) ? (
                      <HeartSolidIcon className="h-4 w-4 text-red-500" />
                    ) : (
                      <HeartIcon className="h-4 w-4 text-gray-600" />
                    )}
                  </button>

                  {/* Template Preview */}
                  <div className={`${view === 'list' ? 'w-48' : 'w-full'} aspect-video bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 relative overflow-hidden`}>
                    {template.preview_url ? (
                      <img
                        src={template.preview_url}
                        alt={template.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <div className="text-center">
                          <div className="text-4xl mb-2">
                            {getTemplateTypeIcon(template.type)}
                          </div>
                          <div className="text-sm text-gray-500">
                            {template.type} template
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Preview Overlay */}
                    <div className="absolute inset-0 bg-black/50 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setPreviewTemplate(template);
                        }}
                      >
                        <EyeIcon className="h-4 w-4 mr-2" />
                        Preview
                      </Button>
                    </div>
                  </div>

                  {/* Template Info */}
                  <div className={`${view === 'list' ? 'flex-1' : ''} p-4`}>
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 line-clamp-1">
                        {template.name}
                      </h3>
                      <Badge
                        variant="outline"
                        size="xs"
                        className={getTypeColor(template.type)}
                      >
                        {template.type}
                      </Badge>
                    </div>
                    
                    {template.description && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                        {template.description}
                      </p>
                    )}
                    
                    {/* Template Stats */}
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center space-x-3">
                        {/* Rating */}
                        <div className="flex items-center space-x-1">
                          <StarSolidIcon className="h-3 w-3 text-yellow-400" />
                          <span>{template.rating.toFixed(1)}</span>
                        </div>
                        
                        {/* Usage Count */}
                        <div className="flex items-center space-x-1">
                          <PlayIcon className="h-3 w-3" />
                          <span>{template.usage_count}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <Badge
                          variant="outline"
                          size="xs"
                          className="text-purple-600 border-purple-300"
                        >
                          {template.category}
                        </Badge>
                      </div>
                    </div>
                    
                    {/* Tags */}
                    {template.tags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {template.tags.slice(0, 3).map((tag, index) => (
                          <Badge key={index} variant="secondary" size="xs">
                            {tag}
                          </Badge>
                        ))}
                        {template.tags.length > 3 && (
                          <Badge variant="secondary" size="xs">
                            +{template.tags.length - 3}
                          </Badge>
                        )}
                      </div>
                    )}
                    
                    {/* Action Buttons */}
                    <div className="mt-3 flex items-center space-x-2">
                      <Button
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTemplateSelect(template);
                        }}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        Use Template
                      </Button>
                      
                      <Tooltip content="Preview Template">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setPreviewTemplate(template);
                          }}
                        >
                          <EyeIcon className="h-4 w-4" />
                        </Button>
                      </Tooltip>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Empty State */}
      {!loading && filteredTemplates.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-12"
        >
          <div className="text-6xl mb-4">🎨</div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            No templates found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {searchQuery ? 'Try adjusting your search terms' : 'No templates match your current filters'}
          </p>
          {searchQuery && (
            <Button
              variant="outline"
              onClick={() => setSearchQuery('')}
            >
              Clear search
            </Button>
          )}
        </motion.div>
      )}

      {/* Template Preview Modal */}
      <Modal
        isOpen={!!previewTemplate}
        onClose={() => setPreviewTemplate(null)}
        title={`Preview: ${previewTemplate?.name}`}
        size="lg"
      >
        {previewTemplate && (
          <TemplatePreview
            template={previewTemplate}
            onSelect={() => {
              handleTemplateSelect(previewTemplate);
              setPreviewTemplate(null);
            }}
            onClose={() => setPreviewTemplate(null)}
          />
        )}
      </Modal>

      {/* Create Template Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="fixed bottom-6 right-6"
      >
        <Tooltip content="Create Custom Template">
          <Button
            size="lg"
            className="rounded-full shadow-lg bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
            onClick={() => {
              // Navigate to template creation
            }}
          >
            <PlusIcon className="h-6 w-6" />
          </Button>
        </Tooltip>
      </motion.div>
    </div>
  );
}

// Helper functions
function getTypeColor(type: TemplateType): string {
  const colors = {
    subtitle: 'border-blue-300 text-blue-700 bg-blue-50',
    video: 'border-green-300 text-green-700 bg-green-50',
    brand: 'border-purple-300 text-purple-700 bg-purple-50'
  };
  return colors[type] || 'border-gray-300 text-gray-700 bg-gray-50';
}

function getTemplateTypeIcon(type: TemplateType): string {
  const icons = {
    subtitle: '💬',
    video: '🎬',
    brand: '🏷️'
  };
  return icons[type] || '📄';
}
