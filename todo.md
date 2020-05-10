Consolidated "runner" and cli
- have slick.util, just need to get it into the shape it needs to be in

Refactor:
solve item deduplication model/item issue.
  right now item subclasses. Needs to happen on realize_item

map steam_id/game_id on concurrent players to auto-wire
conditionally remove whitespace from game url
