EMPTY = '▁'
MILD = '░'
MEDIUM = '▒'
HIGH = '▓'
FULL = '█'

def progress(percent: int) -> str:
  result = ''
  buckets = 10
  bucket_size = 100 // buckets
  third = bucket_size / 3
  for i in range(buckets):
    bottom = i * bucket_size
    top = (i+1) * bucket_size
    if percent <= bottom:
      result += EMPTY
    elif percent >= top:
      result += FULL
    else:
      within_range = (percent - bottom)
      if within_range < third:
        result += MILD
      elif within_range < 2 * third:
        result += MEDIUM
      else:
        result += HIGH
  return result
