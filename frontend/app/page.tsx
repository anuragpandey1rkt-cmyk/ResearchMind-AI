import { Activity, Database, FileText, Search } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ResearchWorkspace } from "@/components/research/research-workspace";

const metrics = [
  { label: "Agents", value: "6", icon: Activity },
  { label: "Vector Collections", value: "2", icon: Database },
  { label: "Report Sections", value: "8", icon: FileText },
  { label: "Search Sources", value: "DuckDuckGo", icon: Search }
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{metric.label}</CardTitle>
              <metric.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold">{metric.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
      <ResearchWorkspace />
    </div>
  );
}
