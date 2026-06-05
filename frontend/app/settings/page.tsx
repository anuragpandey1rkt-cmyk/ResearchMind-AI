import { Database, KeyRound, Server } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const settings = [
  { label: "Backend URL", value: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000", icon: Server },
  { label: "Inference", value: "Groq API via GROQ_API_KEY", icon: KeyRound },
  { label: "Vector Store", value: "ChromaDB persistent collections", icon: Database }
];

export default function SettingsPage() {
  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="mt-1 text-muted-foreground">Runtime configuration is managed through environment variables.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {settings.map((item) => (
          <Card key={item.label}>
            <CardHeader>
              <item.icon className="h-5 w-5 text-primary" />
              <CardTitle>{item.label}</CardTitle>
              <CardDescription>{item.value}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Environment</CardTitle>
          <CardDescription>Set these in Render, Vercel, or local `.env` files.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          {["GROQ_API_KEY", "DATABASE_URL", "SUPABASE_URL", "SUPABASE_ANON_KEY", "NEXT_PUBLIC_API_URL", "CHROMA_PATH"].map((key) => (
            <div key={key} className="space-y-2">
              <Label>{key}</Label>
              <Input readOnly value={key.includes("KEY") ? "************" : key} />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
