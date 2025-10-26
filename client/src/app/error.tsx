"use client";

const Error = ({ error }: { error: Error }) => {
  return (
    <div className="flex flex-col items-center justify-center h-screen text-center px-10">
      <h2 className="text-2xl font-semibold mb-4">Something went wrong.</h2>
      <p className="mb-4 text-red-600">
        {error.message || "Server is currently unavailable."}
      </p>
    </div>
  );
};

export default Error;
