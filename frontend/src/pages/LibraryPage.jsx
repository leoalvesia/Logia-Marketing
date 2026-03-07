import * as Tabs from "@radix-ui/react-tabs";
import { BookOpen, Image, LayoutGrid } from "lucide-react";
import LibraryCopysTab from "@/components/Library/CopysTab";
import LibraryArtTab from "@/components/Library/ArtTab";
import LibraryPostsTab from "@/components/Library/PostsTab";

const TABS = [
  { value: "copies", label: "Copys", icon: BookOpen, component: LibraryCopysTab },
  { value: "art", label: "Arte", icon: Image, component: LibraryArtTab },
  { value: "posts", label: "Posts", icon: LayoutGrid, component: LibraryPostsTab },
];

export default function LibraryPage() {
  return (
    <div className="p-5 md:p-6 max-w-5xl mx-auto space-y-6 animate-[fade-in_0.25s_ease-out]">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-[#F9FAFB]">Biblioteca</h1>
        <p className="text-xs text-[#6B7280] mt-0.5">Todo o conteúdo gerado — copys, artes e posts</p>
      </div>

      {/* Tabs */}
      <Tabs.Root defaultValue="copies">
        {/* Tab list */}
        <Tabs.List className="flex border-b border-[#2E2E2E] gap-0 mb-5">
          {TABS.map(({ value, label, icon: Icon }) => (
            <Tabs.Trigger
              key={value}
              value={value}
              className="flex items-center gap-2 px-4 py-3 text-sm font-medium text-[#6B7280] border-b-2 border-transparent
                         data-[state=active]:border-[#6366F1] data-[state=active]:text-[#F9FAFB]
                         hover:text-[#9CA3AF] transition-all
                         outline-none focus-visible:ring-2 focus-visible:ring-[#6366F1]/50 -mb-px"
            >
              <Icon size={14} />
              {label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        {/* Tab panels */}
        {TABS.map(({ value, component: Component }) => (
          <Tabs.Content key={value} value={value} className="outline-none">
            <Component />
          </Tabs.Content>
        ))}
      </Tabs.Root>
    </div>
  );
}
