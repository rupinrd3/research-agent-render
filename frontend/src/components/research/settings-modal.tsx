/**
 * Settings Modal Component
 * Comprehensive configuration for LLM providers, models, and research parameters.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Sparkles, Zap, Save, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useResearchStore } from '@/store/research-store';
import { useToast } from '@/hooks/use-toast';
import { LLM_PROVIDERS } from '@/lib/constants';
import type { Settings } from '@/types';

interface SettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Comprehensive settings modal for configuring research parameters.
 *
 * Features:
 * - LLM provider selection (OpenAI, Gemini, OpenRouter)
 * - Model selection per provider
 * - Temperature control with visual slider
 * - Max iterations configuration
 * - API key management
 * - Real-time validation
 * - Persistent settings storage
 *
 * @example
 * ```tsx
 * <SettingsModal
 *   open={showSettings}
 *   onOpenChange={setShowSettings}
 * />
 * ```
 */
export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const { settings, updateSettings } = useResearchStore();
  const { toast } = useToast();

  // Local state for form inputs
  const [localSettings, setLocalSettings] = useState<Settings>(settings);
  const [hasChanges, setHasChanges] = useState(false);

  // Update local state when modal opens
  useEffect(() => {
    if (open) {
      // Ensure apiKeys exists (for backwards compatibility)
      const settingsWithDefaults = {
        ...settings,
        apiKeys: settings.apiKeys || {
          openai: '',
          gemini: '',
          openrouter: '',
        },
      };
      setLocalSettings(settingsWithDefaults);
      setHasChanges(false);
    }
  }, [open, settings]);

  // Track changes
  useEffect(() => {
    const changed = JSON.stringify(localSettings) !== JSON.stringify(settings);
    setHasChanges(changed);
  }, [localSettings, settings]);

  const handleSave = () => {
    // Validate settings
    if (!localSettings.llmProvider) {
      toast({
        variant: 'destructive',
        title: 'Validation Error',
        description: 'Please select an LLM provider',
      });
      return;
    }

    if (!localSettings.llmModel) {
      toast({
        variant: 'destructive',
        title: 'Validation Error',
        description: 'Please select a model',
      });
      return;
    }

    // Save settings
    updateSettings(localSettings);

    toast({
      variant: 'success',
      title: 'Settings Saved',
      description: 'Your configuration has been saved successfully',
    });

    onOpenChange(false);
  };

  const handleProviderChange = (provider: 'openai' | 'gemini' | 'openrouter') => {
    const providerConfig = LLM_PROVIDERS.find((p) => p.value === provider);
    setLocalSettings({
      ...localSettings,
      llmProvider: provider,
      llmModel: providerConfig?.models[0] || '',
    });
  };

  const selectedProvider = LLM_PROVIDERS.find(
    (p) => p.value === localSettings.llmProvider
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-slate-900 text-white border border-slate-700 shadow-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl text-white">
            <SettingsIcon className="w-6 h-6 text-indigo-400" />
            Research Settings
          </DialogTitle>
          <DialogDescription className="text-white/80">
            Configure your research assistant's behavior and API connections
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="llm" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="llm">
              <Sparkles className="w-4 h-4 mr-2" />
              LLM Config
            </TabsTrigger>
            <TabsTrigger value="research">
              <Zap className="w-4 h-4 mr-2" />
              Research
            </TabsTrigger>
            <TabsTrigger value="api">API Keys</TabsTrigger>
          </TabsList>

          {/* LLM Configuration Tab */}
          <TabsContent value="llm" className="space-y-6 mt-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="provider" className="text-white mb-2 block">
                  LLM Provider
                </Label>
                <Select
                  value={localSettings.llmProvider}
                  onValueChange={handleProviderChange}
                >
                  <SelectTrigger id="provider">
                    <SelectValue placeholder="Select provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {LLM_PROVIDERS.map((provider) => (
                      <SelectItem key={provider.value} value={provider.value}>
                        <div className="flex items-center gap-2">
                          <span>{provider.label}</span>
                          {provider.value === 'openai' && (
                            <Badge variant="outline" className="text-xs">Recommended</Badge>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-white/70 mt-1">
                  Choose your preferred language model provider
                </p>
              </div>

              <div>
                <Label htmlFor="model" className="text-white mb-2 block">
                  Model
                </Label>
                <Select
                  value={localSettings.llmModel}
                  onValueChange={(value) =>
                    setLocalSettings({ ...localSettings, llmModel: value })
                  }
                  disabled={!selectedProvider}
                >
                  <SelectTrigger id="model">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {selectedProvider?.models.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-white/70 mt-1">
                  {selectedProvider?.value === 'openai' &&
                    'gpt-4.1-mini is the fast default; gpt-5* uses the Responses API with enhanced reasoning.'}
                  {selectedProvider?.value === 'gemini' && 'Gemini 2.5 Flash is highly capable'}
                  {selectedProvider?.value === 'openrouter' &&
                    'Free OpenRouter tier (DeepSeek, MiniMax, Meta-Llama)'}
                </p>
              </div>

              <div>
                <Label htmlFor="temperature" className="text-white mb-2 block">
                  Temperature: {localSettings.temperature.toFixed(2)}
                </Label>
                <div className="flex items-center gap-4">
                  <Slider
                    id="temperature"
                    min={0}
                    max={1}
                    step={0.01}
                    value={[localSettings.temperature]}
                    onValueChange={([value]) =>
                      setLocalSettings({ ...localSettings, temperature: value })
                    }
                    className="flex-1"
                  />
                  <div className="w-16 text-center">
                    <Badge variant="outline">
                      {localSettings.temperature.toFixed(2)}
                    </Badge>
                  </div>
                </div>
                <div className="flex justify-between text-xs text-white/70 mt-1">
                  <span>More Focused</span>
                  <span>More Creative</span>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Research Parameters Tab */}
          <TabsContent value="research" className="space-y-6 mt-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="maxIterations" className="text-white mb-2 block">
                  Max Iterations
                </Label>
                <div className="flex items-center gap-4">
                  <Slider
                    id="maxIterations"
                    min={3}
                    max={20}
                    step={1}
                    value={[localSettings.maxIterations]}
                    onValueChange={([value]) =>
                      setLocalSettings({ ...localSettings, maxIterations: value })
                    }
                    className="flex-1"
                  />
                  <div className="w-16 text-center">
                    <Badge variant="outline" className="text-white">{localSettings.maxIterations}</Badge>
                  </div>
                </div>
                <p className="text-xs text-white/70 mt-1">
                  Maximum number of reasoning iterations (higher = more thorough)
                </p>
              </div>

              <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-700/50">
                <h4 className="font-medium text-white mb-2">Estimated Research Time</h4>
                <p className="text-sm text-white/80">
                  With current settings: ~{(localSettings.maxIterations * 20).toFixed(0)}s - {(localSettings.maxIterations * 30).toFixed(0)}s
                </p>
                <div className="mt-2 flex gap-2">
                  <Badge variant="outline" className="text-xs">
                    Iterations: {localSettings.maxIterations}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    Est. Cost: $0.002-0.01
                  </Badge>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* API Keys Tab */}
          <TabsContent value="api" className="space-y-6 mt-6">
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                <p className="text-sm text-amber-200">
                  🔒 API keys are stored locally in your browser and never sent to our servers
                </p>
              </div>

              <div>
                <Label htmlFor="openaiKey" className="text-white mb-2 block">
                  OpenAI API Key
                </Label>
                <Input
                  id="openaiKey"
                  type="password"
                  placeholder="sk-..."
                  value={localSettings.apiKeys.openai || ''}
                  onChange={(e) =>
                    setLocalSettings({
                      ...localSettings,
                      apiKeys: { ...localSettings.apiKeys, openai: e.target.value },
                    })
                  }
                />
                <p className="text-xs text-white/70 mt-1">
                  Get your key from{' '}
                  <a
                    href="https://platform.openai.com/api-keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-400 hover:underline"
                  >
                    platform.openai.com
                  </a>
                </p>
              </div>

              <div>
                <Label htmlFor="geminiKey" className="text-white mb-2 block">
                  Google Gemini API Key
                </Label>
                <Input
                  id="geminiKey"
                  type="password"
                  placeholder="..."
                  value={localSettings.apiKeys.gemini || ''}
                  onChange={(e) =>
                    setLocalSettings({
                      ...localSettings,
                      apiKeys: { ...localSettings.apiKeys, gemini: e.target.value },
                    })
                  }
                />
                <p className="text-xs text-white/70 mt-1">
                  Get your key from{' '}
                  <a
                    href="https://makersuite.google.com/app/apikey"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-400 hover:underline"
                  >
                    Google AI Studio
                  </a>
                </p>
              </div>

              <div>
                <Label htmlFor="openrouterKey" className="text-white mb-2 block">
                  OpenRouter API Key
                </Label>
                <Input
                  id="openrouterKey"
                  type="password"
                  placeholder="sk-or-..."
                  value={localSettings.apiKeys.openrouter || ''}
                  onChange={(e) =>
                    setLocalSettings({
                      ...localSettings,
                      apiKeys: { ...localSettings.apiKeys, openrouter: e.target.value },
                    })
                  }
                />
                <p className="text-xs text-white/70 mt-1">
                  Get your key from{' '}
                  <a
                    href="https://openrouter.ai/keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-400 hover:underline"
                  >
                    openrouter.ai
                  </a>
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!hasChanges}
            className="bg-gradient-to-r from-indigo-600 to-purple-600"
          >
            <Save className="w-4 h-4 mr-2" />
            Save Settings
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
