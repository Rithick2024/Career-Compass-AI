import React, { useState, useRef, useEffect } from 'react';
import {
  Bot,
  Sparkles,
  Send,
  RefreshCw,
  AlertCircle,
  User,
  Lightbulb,
  GraduationCap,
  Briefcase,
  Trash2,
  Cpu,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/features/auth/context/AuthContext';
import { intelligenceService } from '@/features/student/services/intelligence.service';
import {
  ChatMessage,
  MentorContextSummary,
} from '@/features/student/types/intelligence.types';

const SUGGESTED_PROMPTS = [
  {
    title: 'Backend Developer Prep',
    prompt: 'How can I prepare for a backend developer role on campus?',
    category: 'Career Path',
  },
  {
    title: 'Next Skills to Learn',
    prompt: 'Which skills should I improve next based on my profile?',
    category: 'Skills',
  },
  {
    title: 'Technical Interview Prep',
    prompt: 'Help me prepare for a technical interview for campus placements.',
    category: 'Interviews',
  },
  {
    title: 'Resume Project Idea',
    prompt: 'Suggest a project to demonstrate my skills to campus recruiters.',
    category: 'Projects',
  },
];

interface FormattedMessageProps {
  content: string;
}

function FormattedContent({ content }: FormattedMessageProps) {
  // Simple, robust markdown-like line renderer for bold, headers, code, and bullet points
  const lines = content.split('\n');

  return (
    <div className="space-y-2 text-sm leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={idx} className="h-1" />;
        }

        // Headings: ### or ## or #
        if (trimmed.startsWith('### ')) {
          return (
            <h4 key={idx} className="font-bold text-foreground text-base mt-3 mb-1">
              {trimmed.replace('### ', '')}
            </h4>
          );
        }
        if (trimmed.startsWith('## ')) {
          return (
            <h3 key={idx} className="font-bold text-foreground text-lg mt-3 mb-1 border-b pb-1 border-border/50">
              {trimmed.replace('## ', '')}
            </h3>
          );
        }

        // Bullet points
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          const bulletText = trimmed.substring(2);
          return (
            <div key={idx} className="flex items-start gap-2 ml-1">
              <span className="text-primary mt-1 font-bold">•</span>
              <span className="flex-1">
                <InlineFormatter text={bulletText} />
              </span>
            </div>
          );
        }

        // Numbered lists: e.g. "1. "
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
        if (numMatch) {
          return (
            <div key={idx} className="flex items-start gap-2 ml-1">
              <span className="text-primary font-semibold min-w-[1.2rem]">{numMatch[1]}.</span>
              <span className="flex-1">
                <InlineFormatter text={numMatch[2]} />
              </span>
            </div>
          );
        }

        return (
          <p key={idx} className="text-foreground/90">
            <InlineFormatter text={trimmed} />
          </p>
        );
      })}
    </div>
  );
}

function InlineFormatter({ text }: { text: string }) {
  // Parse **bold** and `code` segments
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);

  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={i} className="font-semibold text-foreground">
              {part.slice(2, -2)}
            </strong>
          );
        }
        if (part.startsWith('`') && part.endsWith('`')) {
          return (
            <code key={i} className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs text-primary">
              {part.slice(1, -1)}
            </code>
          );
        }
        return part;
      })}
    </>
  );
}

export default function StudentMentorPage() {
  const { user } = useAuth();
  const avatarText = user?.email?.substring(0, 2).toUpperCase() || 'ST';
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'model',
      content:
        "👋 Welcome! I am your **Career Compass AI Mentor**.\n\nI provide personalized guidance grounded in your **academic department, registered skills, and current campus placement drives**.\n\nFeel free to ask about role preparation, skill roadmaps, technical interview strategies, or project recommendations. How can I help you today?",
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isQuotaError, setIsQuotaError] = useState(false);
  const [groundedContext, setGroundedContext] = useState<MentorContextSummary | null>(null);
  const [modelUsed, setModelUsed] = useState<string>('gemini-3.8-flash');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || isLoading) return;

    if (text.length > 1500) {
      setError('Message exceeds the 1,500 character limit. Please shorten your question.');
      return;
    }

    setError(null);
    setIsQuotaError(false);
    setInputMessage('');

    const newMessages: ChatMessage[] = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      // Build conversation history (excluding initial greeting and the current message)
      const historyToSend = messages
        .slice(1)
        .slice(-4)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      const res = await intelligenceService.askMentor({
        message: text,
        history: historyToSend,
      });

      setMessages((prev) => [...prev, { role: 'model', content: res.response }]);
      setGroundedContext(res.grounded_context);
      setModelUsed(res.model_used);
    } catch (err: any) {
      console.error('Mentor error:', err);
      const status = err?.response?.status;
      const errorMsg =
        err?.response?.data?.message || err?.message || 'Failed to get guidance from AI Mentor.';

      if (status === 429) {
        setIsQuotaError(true);
        setError('Gemini API quota or rate limit exceeded. Please wait a minute before asking again.');
      } else if (status === 504) {
        setError('The AI request timed out. Please try asking a more specific, concise question.');
      } else if (status === 503) {
        setError('AI Mentor is currently unconfigured. Please notify your platform administrator.');
      } else {
        setError(errorMsg);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: 'model',
        content:
          "👋 Chat cleared! I am your **Career Compass AI Mentor**.\n\nAsk me any question regarding your campus placement prep, target roles, or technical skills.",
      },
    ]);
    setError(null);
    setIsQuotaError(false);
  };

  return (
    <AppLayout role="student" userName={user?.email || 'Student'} userRole="Student" avatarText={avatarText}>
      <PageContainer>
        <PageHeader
          title="AI Career Mentor"
          description="Personalized career coaching and placement preparation grounded in your verified academic and skill profile."
          action={
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1.5 py-1 px-2.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                Active
              </Badge>
              <Badge variant="secondary" className="gap-1.5 py-1 px-2.5 font-mono text-xs">
                <Cpu className="h-3.5 w-3.5 text-primary" />
                {modelUsed}
              </Badge>
              {messages.length > 1 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearChat}
                  className="text-muted-foreground hover:text-destructive h-8 px-2"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              )}
            </div>
          }
        />

        {/* Profile Grounding Info Banner */}
        {groundedContext && (
          <div className="mb-4 rounded-xl border bg-card/60 backdrop-blur-sm p-3.5 text-xs text-muted-foreground shadow-sm">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <span className="font-semibold text-foreground flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                Grounded Profile Context:
              </span>
              {groundedContext.department && (
                <span className="flex items-center gap-1">
                  <GraduationCap className="h-3.5 w-3.5 text-muted-foreground" />
                  {groundedContext.department}
                </span>
              )}
              {groundedContext.graduation_year && (
                <span>Class of {groundedContext.graduation_year}</span>
              )}
              <span className="flex items-center gap-1">
                <Layers className="h-3.5 w-3.5 text-muted-foreground" />
                {groundedContext.skills_count} Skills Registered
              </span>
              <span className="flex items-center gap-1">
                <Briefcase className="h-3.5 w-3.5 text-muted-foreground" />
                {groundedContext.active_campus_jobs_count} Active Campus Drives
              </span>
            </div>
          </div>
        )}

        {/* Suggested Prompt Chips */}
        {messages.length <= 2 && (
          <div className="mb-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Lightbulb className="h-3.5 w-3.5 text-amber-500" />
              Suggested Placement Questions
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
              {SUGGESTED_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(item.prompt)}
                  disabled={isLoading}
                  className="group text-left p-3 rounded-xl border bg-card hover:bg-accent/50 hover:border-primary/40 transition-all duration-200 text-xs shadow-sm flex flex-col justify-between"
                >
                  <span className="font-medium text-foreground group-hover:text-primary transition-colors flex items-center justify-between">
                    {item.title}
                    <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity transform group-hover:translate-x-0.5" />
                  </span>
                  <span className="text-muted-foreground line-clamp-2 mt-1">
                    "{item.prompt}"
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat Stream Card */}
        <Card className="flex flex-col h-[560px] shadow-sm border-border">
          <CardContent className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
            {messages.map((msg, index) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={index}
                  className={`flex gap-3 max-w-[85%] sm:max-w-[78%] ${
                    isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                      isUser
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'bg-primary/10 text-primary border border-primary/20'
                    }`}
                  >
                    {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>

                  {/* Message Bubble */}
                  <div
                    className={`rounded-2xl px-4 py-3 shadow-sm ${
                      isUser
                        ? 'bg-primary text-primary-foreground rounded-tr-none'
                        : 'bg-muted/60 border border-border/60 rounded-tl-none'
                    }`}
                  >
                    {isUser ? (
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <FormattedContent content={msg.content} />
                    )}
                  </div>
                </div>
              );
            })}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex gap-3 max-w-[75%] mr-auto items-center">
                <div className="h-8 w-8 rounded-full flex items-center justify-center shrink-0 bg-primary/10 text-primary border border-primary/20">
                  <Bot className="h-4 w-4 animate-spin" />
                </div>
                <div className="rounded-2xl rounded-tl-none px-4 py-3 bg-muted/60 border border-border/60">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                    <span>Analyzing your profile and formulating guidance...</span>
                  </div>
                </div>
              </div>
            )}

            {/* Error Message Box */}
            {error && (
              <div className="p-3.5 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-xs flex items-start gap-2.5">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold">
                    {isQuotaError ? 'Provider Quota Limit Reached' : 'Service Notice'}
                  </p>
                  <p className="mt-0.5 text-muted-foreground">{error}</p>
                  {isQuotaError && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSendMessage()}
                      className="mt-2 h-7 text-xs border-destructive/30 hover:bg-destructive/10"
                    >
                      <RefreshCw className="h-3 w-3 mr-1" />
                      Try Again
                    </Button>
                  )}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </CardContent>

          {/* Chat Input Bar */}
          <div className="border-t p-3 sm:p-4 bg-card/60 backdrop-blur-sm rounded-b-xl">
            <div className="flex flex-col gap-2">
              <div className="relative">
                <Textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a question about your career, interview prep, or skills... (Press Enter to send)"
                  disabled={isLoading}
                  maxLength={1500}
                  rows={2}
                  className="pr-12 resize-none min-h-[60px] text-sm rounded-xl border-muted-foreground/20 focus-visible:ring-primary"
                />
                <Button
                  onClick={() => handleSendMessage()}
                  disabled={!inputMessage.trim() || isLoading}
                  size="icon"
                  className="absolute right-2 bottom-2 h-8 w-8 rounded-lg shadow-sm"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>

              <div className="flex justify-between items-center text-[11px] text-muted-foreground px-1">
                <span>Shift + Enter for a new line</span>
                <span className={inputMessage.length > 1400 ? 'text-destructive font-semibold' : ''}>
                  {inputMessage.length} / 1500
                </span>
              </div>
            </div>
          </div>
        </Card>
      </PageContainer>
    </AppLayout>
  );
}
