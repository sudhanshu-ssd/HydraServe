import { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { chatApi } from '../../api/chat';
import { modelsApi } from '../../api/models';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Send, Key, Settings2, Sparkles, AlertCircle } from 'lucide-react';
import type { ChatRequest } from '../../types';

export function Playground() {
  const [apiKey, setApiKey] = useState(localStorage.getItem('playground_api_key') || '');
  const [prompt, setPrompt] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful AI assistant.');
  const [model, setModel] = useState('');
  const [temperature, setTemperature] = useState('0.7');
  const [maxTokens, setMaxTokens] = useState('512');
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string; latency?: number }[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Save API key to local storage
  useEffect(() => {
    localStorage.setItem('playground_api_key', apiKey);
  }, [apiKey]);

  const { data: modelsList } = useQuery({
    queryKey: ['models'],
    queryFn: modelsApi.list,
  });

  // Set default model if not set and models are loaded
  useEffect(() => {
    if (modelsList && modelsList.length > 0 && !model) {
      setModel(modelsList[0].model_name);
    }
  }, [modelsList, model]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: (data: ChatRequest) => chatApi.send(apiKey, data),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response },
      ]);
    },
    onError: (err: any) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${err.response?.data?.detail || err.message}` },
      ]);
    },
  });

  const handleSend = () => {
    if (!prompt.trim() || !apiKey.trim() || !model) return;

    const userMessage = prompt;
    setPrompt('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);

    chatMutation.mutate({
      prompt: userMessage,
      system_prompt: systemPrompt,
      model,
      model_temp: parseFloat(temperature),
      max_tokens: parseInt(maxTokens, 10),
    });
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-6rem)]">
      {/* Left sidebar - Settings */}
      <div className="w-full lg:w-1/3 xl:w-1/4 flex flex-col gap-6 overflow-y-auto pr-2 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Playground</h2>
          <p className="text-sm text-muted-foreground">Test your API keys and models</p>
        </div>

        <Card className="bg-card/50 backdrop-blur-sm border-white/[0.04]">
          <CardHeader className="pb-4">
            <CardTitle className="text-base flex items-center gap-2">
              <Key className="h-4 w-4 text-amber-500" /> API Authentication
            </CardTitle>
            <CardDescription>Enter a valid API key to make requests</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Label htmlFor="apiKey">HydraServe API Key</Label>
              <Input
                id="apiKey"
                type="password"
                placeholder="hs_..."
                value={apiKey}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApiKey(e.target.value)}
                className="font-mono"
              />
              {!apiKey && (
                <p className="text-xs text-amber-500 flex items-center gap-1 mt-1">
                  <AlertCircle className="h-3 w-3" /> API key is required
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-sm border-white/[0.04]">
          <CardHeader className="pb-4">
            <CardTitle className="text-base flex items-center gap-2">
              <Settings2 className="h-4 w-4 text-primary" /> Parameters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Model</Label>
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent className="bg-card border-white/[0.08]">
                  {modelsList?.map((m) => (
                    <SelectItem key={m.model_id} value={m.model_name}>
                      {m.provider}: {m.model_name}
                    </SelectItem>
                  ))}
                  {(!modelsList || modelsList.length === 0) && (
                    <SelectItem value="none" disabled>
                      No models available
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="systemPrompt">System Prompt</Label>
              <textarea
                id="systemPrompt"
                value={systemPrompt}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setSystemPrompt(e.target.value)}
                className="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="temperature">Temperature</Label>
                <Input
                  id="temperature"
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={temperature}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTemperature(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxTokens">Max Tokens</Label>
                <Input
                  id="maxTokens"
                  type="number"
                  min="1"
                  max="4096"
                  value={maxTokens}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMaxTokens(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Right panel - Chat */}
      <Card className="flex-1 flex flex-col bg-card/30 backdrop-blur-sm border-white/[0.04] overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground space-y-4 opacity-50">
              <Sparkles className="h-12 w-12" />
              <p>Configure your settings and send a message to start testing</p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col ${
                  msg.role === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground rounded-tr-sm'
                      : msg.content.startsWith('Error:') 
                        ? 'bg-destructive/10 text-destructive rounded-tl-sm border border-destructive/20'
                        : 'bg-white/[0.04] text-foreground rounded-tl-sm border border-white/[0.08]'
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                </div>
                <span className="text-xs text-muted-foreground mt-1 px-1">
                  {msg.role === 'user' ? 'You' : 'Assistant'}
                </span>
              </div>
            ))
          )}
          {chatMutation.isPending && (
            <div className="flex flex-col items-start">
              <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white/[0.04] rounded-tl-sm border border-white/[0.08]">
                <div className="flex gap-1">
                  <div className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
              <span className="text-xs text-muted-foreground mt-1 px-1">Assistant is typing...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="p-4 border-t border-white/[0.04] bg-card/50">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex gap-2"
          >
            <Input
              placeholder={apiKey ? "Type your prompt here..." : "Enter an API key first to send messages"}
              value={prompt}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPrompt(e.target.value)}
              className="flex-1 bg-white/[0.02]"
              disabled={chatMutation.isPending || !apiKey}
            />
            <Button
              type="submit"
              size="icon"
              disabled={!prompt.trim() || chatMutation.isPending || !apiKey}
              className="bg-primary hover:bg-primary/90"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
