import type { NewsItem, SocialMention } from "../types";

interface Props {
  newsItems: NewsItem[];
  socialMentions: SocialMention[];
}

export function NewsFeed({ newsItems, socialMentions }: Props) {
  const allItems = [
    ...newsItems.map((n) => ({ ...n, type: "news" as const })),
    ...socialMentions.map((s) => ({ ...s, type: "social" as const, title: s.content.slice(0, 100) })),
  ];

  if (allItems.length === 0) return null;

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h3 className="font-semibold mb-3">Recent News & Social</h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {allItems.slice(0, 10).map((item, i) => (
          <a
            key={i}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-2 hover:bg-gray-50 rounded"
          >
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">{item.source}</span>
              <span className="text-sm">{item.title}</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
