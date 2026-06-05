import Link from "next/link";
import { BookOpenCheck, Clock3, FileSearch, FileUp, Home, Settings, Sparkles } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

const nav = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/new-research", label: "New", icon: Sparkles },
  { href: "/gap-detector", label: "Gaps", icon: FileSearch },
  { href: "/upload", label: "Upload", icon: FileUp },
  { href: "/history", label: "History", icon: Clock3 },
  { href: "/settings", label: "Settings", icon: Settings }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r bg-card lg:block">
        <div className="flex h-16 items-center gap-3 border-b px-5">
          <BookOpenCheck className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">ResearchMind</span>
        </div>
        <nav className="space-y-1 p-3">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex h-10 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur md:px-6">
          <div className="flex items-center gap-3 lg:hidden">
            <BookOpenCheck className="h-5 w-5 text-primary" />
            <span className="font-semibold">ResearchMind</span>
          </div>
          <div className="hidden text-sm text-muted-foreground lg:block">Agentic AI Research Assistant</div>
          <ThemeToggle />
        </header>
        <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">{children}</main>
      </div>
    </div>
  );
}
