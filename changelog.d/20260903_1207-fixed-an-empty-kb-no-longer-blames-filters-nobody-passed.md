- **An empty KB no longer blames filters the user never passed.** When retrieval found nothing to
  search, the confidence reason read *"nothing matched the filters"* whether or not any filter had
  been given — so the first search against a KB that had just been created, or one whose every
  document had been retired, sent the user looking for a filter that did not exist. The two states
  need opposite actions and now say so: *"nothing matched the filters"* when the caller narrowed
  something, *"this KB has no active documents to search"* when they did not.
