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
  Plus,
  MessageSquare,
  Clock,
  ChevronLeft,
  ChevronRight,
  FileText,
  CheckCircle2,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageHeader, PageContainer } from '@/components/common/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/features/auth/context/AuthContext';
import { intelligenceService } from '@/features/student/services/intelligence.service';
import {
  ChatMessage,
  MentorContextSummary,
  MentorSessionSummary,
} from '@/features/student/types/intelligence.types';

const WELCOME_MESSAGE: ChatMessage = {
  role: 'model',
  content:
    "👋 Welcome! I am your **Career Compass AI Mentor**.\n\nI am personalized and grounded in your **verified academic department, registered skills, campus job applications, and active placement drives**.\n\nFeel free to ask me about:\n* 💻 **Your skills profile:** e.g., *'What are my registered skills?'*\n* 💼 **Active campus placement drives:** e.g., *'What jobs are available for me?'*\n* 📊 **Your application progress:** e.g., *'What is my applied count and current status?'*\n* 🚀 **Placement preparation roadmap:** e.g., *'How can I prepare for technical interviews?'*\n\nHow can I help you today?",
};

const APP_QUICK_PROMPTS = [
  {
    title: 'My Registered Skills',
    prompt: 'What are my registered skills and proficiency levels on Career Compass?',
    badge: 'Skills',
  },
  {
    title: 'Jobs Available For Me',
    prompt: 'What campus placement jobs are currently available for my department and CGPA?',
    badge: 'Jobs',
  },
  {
    title: 'Applied Count & Status',
    prompt: 'How many jobs have I applied to and what is my current application status?',
    badge: 'Applications',
  },
  {
    title: 'Placement Roadmap',
    prompt: 'Based on my skills, what is the best roadmap to crack upcoming technical interviews?',
    badge: 'Roadmap',
  },
];

interface FormattedMessageProps {
  content: string;
}

function FormattedContent({ content }: FormattedMessageProps) {
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

  // Chat State
  const [sessions, setSessions] = useState<MentorSessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isQuotaError, setIsQuotaError] = useState(false);
  const [groundedContext, setGroundedContext] = useState<MentorContextSummary | null>(null);
  const [modelUsed, setModelUsed] = useState<string>('gemini-3.5-flash');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Load Sessions on Mount
  useEffect(() => {
    loadSessions(true);
  }, []);

  const loadSessions = async (autoSelectFirst = false) => {
    try {
      setIsLoadingSessions(true);
      const data = await intelligenceService.getMentorSessions();
      setSessions(data);
      if (autoSelectFirst && data.length > 0) {
        loadSessionDetail(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load mentor sessions:', err);
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const loadSessionDetail = async (sessionId: number) => {
    try {
      setIsLoading(true);
      setError(null);
      const detail = await intelligenceService.getMentorSession(sessionId);
      setActiveSessionId(detail.id);
      if (detail.messages && detail.messages.length > 0) {
        setMessages(
          detail.messages.map((m) => ({
            role: m.role as 'user' | 'model',
            content: m.content,
            model_used: m.model_used || undefined,
            created_at: m.created_at,
          }))
        );
      } else {
        setMessages([WELCOME_MESSAGE]);
      }
    } catch (err: any) {
      console.error('Failed to load session details:', err);
      setError('Failed to load conversation history.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setIsQuotaError(false);
      const newSession = await intelligenceService.createMentorSession();
      setActiveSessionId(newSession.id);
      setMessages([WELCOME_MESSAGE]);
      await loadSessions(false);
    } catch (err) {
      console.error('Failed to create new session:', err);
      // Fallback: reset local state to welcome message
      setActiveSessionId(null);
      setMessages([WELCOME_MESSAGE]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: number) => {
    e.stopPropagation();
    try {
      await intelligenceService.deleteMentorSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([WELCOME_MESSAGE]);
      }
    } catch (err) {
      console.error('Failed to delete chat session:', err);
    }
  };

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

    // Append user message immediately
    const newMessages: ChatMessage[] = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      // Clean request: Send only the message and session_id!
      // The backend manages conversation persistence and grounding automatically.
      const res = await intelligenceService.askMentor({
        message: text,
        session_id: activeSessionId,
      });

      if (res.session_id) {
        setActiveSessionId(res.session_id);
      }

      setMessages((prev) => [
        ...prev,
        { role: 'model', content: res.response, model_used: res.model_used },
      ]);
      setGroundedContext(res.grounded_context);
      setModelUsed(res.model_used);

      // Refresh session list in background to update titles and message counts
      loadSessions(false);
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

  const activeSessionTitle =
    sessions.find((s) => s.id === activeSessionId)?.title || 'Current Conversation';

  return (
    <AppLayout role="student" userName={user?.email || 'Student'} userRole="Student" avatarText={avatarText}>
      <PageContainer>
        <PageHeader
          title="AI Career Mentor"
          description="Personalized career guidance grounded in your registered skills, active applications, and campus placement drives."
          action={
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="gap-1.5 h-8 text-xs sm:hidden"
              >
                <MessageSquare className="h-3.5 w-3.5" />
                History
              </Button>
              <Button
                onClick={handleNewChat}
                size="sm"
                className="gap-1.5 h-8 bg-primary hover:bg-primary/90 text-primary-foreground text-xs shadow-sm"
              >
                <Plus className="h-3.5 w-3.5" />
                New Chat
              </Button>
              <Badge variant="outline" className="hidden sm:inline-flex gap-1.5 py-1 px-2.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                Active
              </Badge>
              <Badge variant="secondary" className="gap-1.5 py-1 px-2.5 font-mono text-xs">
                <Cpu className="h-3.5 w-3.5 text-primary" />
                {modelUsed}
              </Badge>
            </div>
          }
        />

        {/* Profile Grounding Info Banner */}
        {groundedContext && (
          <div className="mb-4 rounded-xl border bg-card/60 backdrop-blur-sm p-3.5 text-xs text-muted-foreground shadow-sm">
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
              <span className="font-semibold text-foreground flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                Grounded Platform Profile:
              </span>
              {groundedContext.department && (
                <span className="flex items-center gap-1">
                  <GraduationCap className="h-3.5 w-3.5 text-muted-foreground" />
                  {groundedContext.department}
                </span>
              )}
              {groundedContext.graduation_year && (
                <span>Batch of {groundedContext.graduation_year}</span>
              )}
              <span className="flex items-center gap-1">
                <Layers className="h-3.5 w-3.5 text-muted-foreground" />
                {groundedContext.skills_count} Skills Registered
              </span>
              <span className="flex items-center gap-1">
                <Briefcase className="h-3.5 w-3.5 text-muted-foreground" />
                {groundedContext.active_campus_jobs_count} Campus Drives
              </span>
              <span className="flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                {groundedContext.applied_jobs_count ?? 0} Applications Submitted
              </span>
              {groundedContext.is_placed && (
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 text-[10px] py-0 px-1.5">
                  Placed 🎉
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Quick App Inquiry Chips */}
        {messages.length <= 2 && (
          <div className="mb-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Lightbulb className="h-3.5 w-3.5 text-amber-500" />
              Quick Questions Grounded in Your Profile
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
              {APP_QUICK_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(item.prompt)}
                  disabled={isLoading}
                  className="group text-left p-3 rounded-xl border bg-card hover:bg-accent/50 hover:border-primary/40 transition-all duration-200 text-xs shadow-sm flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-foreground group-hover:text-primary transition-colors">
                      {item.title}
                    </span>
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                      {item.badge}
                    </Badge>
                  </div>
                  <span className="text-muted-foreground line-clamp-2">
                    "{item.prompt}"
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Main Chat Workspace Layout (Sidebar + Chat Pane) */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 items-start">
          {/* Chat History Sidebar */}
          <Card
            className={`${
              isSidebarOpen ? 'block' : 'hidden'
            } lg:block lg:col-span-1 h-[600px] flex flex-col border-border shadow-sm overflow-hidden`}
          >
            <div className="p-3 border-b bg-muted/30 flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <MessageSquare className="h-3.5 w-3.5 text-primary" />
                Chat History
              </span>
              <Button
                onClick={handleNewChat}
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs text-primary hover:text-primary hover:bg-primary/10 gap-1"
              >
                <Plus className="h-3 w-3" />
                New
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {isLoadingSessions && sessions.length === 0 ? (
                <div className="p-4 text-center text-xs text-muted-foreground">
                  Loading chats...
                </div>
              ) : sessions.length === 0 ? (
                <div className="p-4 text-center text-xs text-muted-foreground">
                  <p>No previous conversations.</p>
                  <p className="mt-1 text-[11px]">Start a new chat to begin!</p>
                </div>
              ) : (
                sessions.map((s) => {
                  const isActive = s.id === activeSessionId;
                  return (
                    <div
                      key={s.id}
                      onClick={() => loadSessionDetail(s.id)}
                      className={`group flex items-center justify-between p-2.5 rounded-lg text-xs cursor-pointer transition-colors border ${
                        isActive
                          ? 'bg-primary/10 border-primary/30 text-foreground font-medium'
                          : 'border-transparent hover:bg-muted/60 text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      <div className="flex-1 min-w-0 pr-2">
                        <p className="truncate font-medium leading-tight">{s.title}</p>
                        <div className="flex items-center gap-2 mt-1 text-[10px] text-muted-foreground">
                          <span>{s.message_count} msgs</span>
                          <span>•</span>
                          <span>{new Date(s.updated_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => handleDeleteSession(e, s.id)}
                        className="h-6 w-6 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive hover:bg-destructive/10 shrink-0 transition-opacity"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  );
                })
              )}
            </div>
          </Card>

          {/* Active Chat Stream Card */}
          <Card
            className={`${
              isSidebarOpen ? 'lg:col-span-3' : 'lg:col-span-4'
            } flex flex-col h-[600px] shadow-sm border-border overflow-hidden`}
          >
            {/* Stream Header */}
            <div className="px-4 py-2.5 border-b bg-muted/20 flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <Bot className="h-4 w-4 text-primary shrink-0" />
                <span className="text-xs font-medium text-foreground truncate">
                  {activeSessionTitle}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNewChat}
                  className="h-7 text-xs text-muted-foreground hover:text-foreground gap-1"
                >
                  <Plus className="h-3 w-3" />
                  New Chat
                </Button>
              </div>
            </div>

            {/* Messages Content */}
            <CardContent className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
              {messages.map((msg, index) => {
                const isUser = msg.role === 'user';
                return (
                  <div
                    key={index}
                    className={`flex gap-3 max-w-[88%] sm:max-w-[80%] ${
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
                      <span>Consulting Career Compass intelligence and formulating advice...</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Box */}
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
            <div className="border-t p-3 sm:p-4 bg-card/60 backdrop-blur-sm">
              <div className="flex flex-col gap-2">
                <div className="relative">
                  <Textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about your skills, campus jobs, applications, or interview roadmaps... (Enter to send)"
                    disabled={isLoading}
                    maxLength={1500}
                    rows={2}
                    className="pr-12 resize-none min-h-[58px] text-sm rounded-xl border-muted-foreground/20 focus-visible:ring-primary"
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
                  <span>Shift + Enter for a new line • Powered by {modelUsed}</span>
                  <span className={inputMessage.length > 1400 ? 'text-destructive font-semibold' : ''}>
                    {inputMessage.length} / 1500
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </PageContainer>
    </AppLayout>
  );
}

