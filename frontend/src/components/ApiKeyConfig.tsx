'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { Key, Loader2, CheckCircle, XCircle } from 'lucide-react';

interface ApiKeyConfigProps {
  onKeyValidated: (key: string) => void;
}

export function ApiKeyConfig({ onKeyValidated }: ApiKeyConfigProps) {
  const [apiKey, setApiKey] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;

    setIsValidating(true);
    setValidationResult('idle');
    setErrorMessage('');

    try {
      const result = await api.validateApiKey(apiKey);
      if (result.isValid) {
        setValidationResult('success');
        setTimeout(() => onKeyValidated(apiKey), 1000);
      } else {
        setValidationResult('error');
        setErrorMessage('Invalid API key. Please check your key and try again.');
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
        <div className="mx-auto mb-4 w-16 h-16 bg-sage-500/10 rounded-full flex items-center justify-center">
          <Key className="w-8 h-8 text-sage-500" />
        </div>
        <CardTitle className="text-2xl font-bold text-sage-400">
          Welcome to SAGE
        </CardTitle>
        <CardDescription className="text-sage-300">
          AI-powered video comparison with TwelveLabs
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="api-key" className="block text-sm font-medium text-sage-400 mb-2">
              TwelveLabs API Key
            </label>
            <input
              id="api-key"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key"
              className="w-full px-3 py-2 border border-sage-200 rounded-md bg-white text-sage-400 placeholder-sage-300 focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent"
              required
            />
          </div>
          
          {validationResult === 'error' && (
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <XCircle className="w-4 h-4" />
              {errorMessage}
            </div>
          )}
          
          {validationResult === 'success' && (
            <div className="flex items-center gap-2 text-green-600 text-sm">
              <CheckCircle className="w-4 h-4" />
              API key validated successfully!
            </div>
          )}
          
          <Button
            type="submit"
            disabled={isValidating || !apiKey.trim()}
            className="w-full bg-sage-500 hover:bg-sage-600 text-white disabled:opacity-50"
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
        
        <div className="mt-6 text-xs text-sage-300 text-center">
          <p>Don&apos;t have an API key?</p>
          <a
            href="https://twelvelabs.io/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sage-500 hover:text-sage-400 underline"
          >
            Get one from TwelveLabs
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
