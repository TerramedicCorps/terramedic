// Shared constants for OrganizationCard, OrganizationGrid, and
// OrganizationGridSkeleton. Keeping them here prevents the components
// from drifting — the grid passes actionText through to each card and
// the skeleton's layout must match the grid's so cards don't reflow
// when streamed results replace the loading state.
export const ORG_GRID_CONTAINER_CLASS = 'flex flex-wrap justify-center gap-6';
export const ORG_CARD_WRAPPER_CLASS = 'w-full sm:w-72';
export const DEFAULT_ORG_ACTION_TEXT = 'Visit Website';
