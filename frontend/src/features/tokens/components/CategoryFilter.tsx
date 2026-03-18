import { useQuery } from "@tanstack/react-query";
import { fetchCategories } from "@/services/tokens.service";
import { useTableStore } from "@/store/tableStore";
import { cn } from "@/lib/utils";

/**
 * CategoryFilter — chip bar to include/exclude token categories.
 *
 * Fetches available categories from `GET /rankings/categories` and renders
 * them as toggle buttons. Excluded categories are visually dimmed and marked
 * with `data-excluded="true"`. Clicking toggles the exclusion state via
 * the tableStore.
 */
export function CategoryFilter() {
  const { excludeCategories, setExcludeCategories, resetFilters } =
    useTableStore();

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
    staleTime: 60_000,
  });

  function toggleCategory(category: string) {
    if (excludeCategories.includes(category)) {
      setExcludeCategories(excludeCategories.filter((c) => c !== category));
    } else {
      setExcludeCategories([...excludeCategories, category]);
    }
  }

  if (categories.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Category filters">
      {categories.map(({ category, count }) => {
        const isExcluded = excludeCategories.includes(category);
        return (
          <button
            key={category}
            type="button"
            data-testid="category-chip"
            data-excluded={isExcluded ? "true" : undefined}
            aria-label={`${category} (${count})`}
            onClick={() => toggleCategory(category)}
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-colors",
              isExcluded
                ? "bg-muted/50 text-muted-foreground line-through opacity-50"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
            )}
          >
            {category}
            <span
              className={cn(
                "rounded-full px-1.5 text-[10px]",
                isExcluded ? "bg-muted" : "bg-background/50",
              )}
            >
              {count}
            </span>
          </button>
        );
      })}

      <button
        type="button"
        aria-label="Reset filters"
        onClick={resetFilters}
        className="ml-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
      >
        Reset filters
      </button>
    </div>
  );
}
