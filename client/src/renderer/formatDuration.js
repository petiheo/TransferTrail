export const formatDuration = (duration) => {
  const milliseconds = duration % 1000;
  const seconds = Math.floor((duration / 1000) % 60);
  const minutes = Math.floor((duration / (1000 * 60)) % 60);
  const hours = Math.floor((duration / (1000 * 60 * 60)) % 24);

  const pad = (num) => num.toString().padStart(2, '0');
  const formattedMs = milliseconds.toString().padStart(3, '0');

  if (hours > 0) {
      return `Time taken: ${hours}:${pad(minutes)}:${pad(seconds)}.${formattedMs} h`;
  } else if (minutes > 0) {
      return `Time taken: ${minutes}:${pad(seconds)}.${formattedMs} m`;
  } else {
      return `Time taken: ${seconds}.${formattedMs} s`;
  }
};