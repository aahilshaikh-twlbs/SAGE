'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { Key, Loader2, CheckCircle, XCircle } from 'lucide-react';

interface ApiKeyConfigProps {
  onKeysValidated: (twelveLabsKey: string, openaiKey: string) => void;
}

export function ApiKeyConfig({ onKeysValidated }: ApiKeyConfigProps) {
  const [twelveLabsKey, setTwelveLabsKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!twelveLabsKey.trim()) return;

    setIsValidating(true);
    setValidationResult('idle');
    setErrorMessage('');

    try {
      const result = await api.validateApiKey(twelveLabsKey);
      if (result.isValid) {
        setValidationResult('success');
        setTimeout(() => onKeysValidated(twelveLabsKey, openaiKey), 1000);
      } else {
        setValidationResult('error');
        setErrorMessage('Invalid TwelveLabs API key. Please check your key and try again.');
      }
    } catch {
      setValidationResult('error');
      setErrorMessage('Failed to validate API key. Please check your connection and try again.');
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <div className="mx-auto mb-4 w-16 h-16 bg-blue/10 rounded-full flex items-center justify-center">
          <Key className="w-8 h-8 text-blue" />
        </div>
        <CardTitle className="text-2xl font-bold text-charcoal">
          Welcome to SAGE
        </CardTitle>
        <CardDescription className="text-ash">
          AI-powered video comparison with TwelveLabs & OpenAI
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="twelvelabs-key" className="block text-sm font-medium text-charcoal mb-2">
              TwelveLabs API Key *
            </label>
            <input
              id="twelvelabs-key"
              type="password"
              value={twelveLabsKey}
              onChange={(e) => setTwelveLabsKey(e.target.value)}
              placeholder="Enter your TwelveLabs API key"
              className="w-full px-3 py-2 border border-smoke rounded-md bg-white text-charcoal placeholder-ash focus:outline-none focus:ring-2 focus:ring-blue focus:border-transparent"
              required
            />
            <p className="text-xs text-ash mt-1">Required for video embedding generation</p>
          </div>

          <div>
            <label htmlFor="openai-key" className="block text-sm font-medium text-charcoal mb-2">
              OpenAI API Key
            </label>
            <input
              id="openai-key"
              type="password"
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder="Enter your OpenAI API key (optional)"
              className="w-full px-3 py-2 border border-smoke rounded-md bg-white text-charcoal placeholder-ash focus:outline-none focus:ring-2 focus:ring-blue focus:border-transparent"
            />
            <p className="text-xs text-ash mt-1">Optional: Enables AI-powered analysis summaries</p>
          </div>
          
          {validationResult === 'error' && (
            <div className="flex items-center gap-2 text-error text-sm">
              <XCircle className="w-4 h-4" />
              {errorMessage}
            </div>
          )}
          
          {validationResult === 'success' && (
            <div className="flex items-center gap-2 text-success text-sm">
              <CheckCircle className="w-4 h-4" />
              API key validated successfully!
            </div>
          )}
          
          <Button
            type="submit"
            disabled={isValidating || !twelveLabsKey.trim()}
            className="w-full bg-blue hover:bg-blue-dark text-white disabled:opacity-50"
          >
            {isValidating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Validating...
              </>
            ) : (
              'Validate & Continue'
            )}
          </Button>
        </form>
        
        <div className="mt-6 text-xs text-ash text-center">
          <p>Don&apos;t have an API key?</p>
          <a
            href="https://twelvelabs.io/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue hover:text-blue-light underline"
          >
            Get one from TwelveLabs
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
